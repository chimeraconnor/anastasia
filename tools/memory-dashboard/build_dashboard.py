#!/usr/bin/env python3
"""
Memory Dashboard - Visualize OpenClaw memory embeddings as an interactive 2D graph.

Generates: dashboard.html with colored bubbles (clusters) and semantic edges.
"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict
import umap
import plotly.graph_objects as go
from sklearn.metrics.pairwise import cosine_similarity

# Optional HDBSCAN clustering
try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    print("⚠ HDBSCAN not available - skipping semantic clustering")

# Configuration
DB_PATH = Path.home() / ".openclaw/memory/main.sqlite"  # Adjust agentId if needed
OUTPUT_DIR = Path.home() / ".openclaw/workspace/tools/memory-dashboard"
OUTPUT_FILE = OUTPUT_DIR / "dashboard.html"

# UMAP Settings
UMAP_N_COMPONENTS = 2
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.1

# HDBSCAN Settings (clustering)
HDBSCAN_MIN_CLUSTER_SIZE = 3
HDBSCAN_MIN_SAMPLES = 5

# Edge Settings (similarity threshold for drawing edges)
EDGE_SIMILARITY_THRESHOLD = 0.75  # Only show edges for very similar chunks
MAX_EDGES = 100  # Cap to avoid clutter

# Node Size
NODE_SIZE = 12
NODE_OPACITY = 0.8


def get_embeddings(db_path: Path) -> Tuple[np.ndarray, List[Dict]]:
    """
    Query SQLite for chunk embeddings and metadata.

    Returns:
        embeddings: numpy array of shape (n_chunks, embedding_dim)
        metadata: list of dicts with chunk_id, file_path, line_start, line_end, content
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Memory database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query chunks table - match actual schema from OpenClaw
    cursor.execute("""
        SELECT id, embedding, path, start_line, end_line, text
        FROM chunks
        ORDER BY id
    """)

    rows = cursor.fetchall()

    if not rows:
        raise ValueError("No chunks found in database")

    embeddings = []
    metadata = []

    for row in rows:
        chunk_id, embedding_json, file_path, start_line, end_line, content = row

        # Parse embedding from JSON
        if isinstance(embedding_json, str):
            embedding = json.loads(embedding_json)
        elif isinstance(embedding_json, bytes):
            embedding = json.loads(embedding_json.decode('utf-8'))
        else:
            embedding = list(embedding_json)

        embeddings.append(embedding)
        metadata.append({
            "chunk_id": chunk_id,
            "file_path": file_path,
            "line_start": start_line,
            "line_end": end_line,
            "content": content[:200] + "..." if len(content) > 200 else content,  # Truncate for hover
        })

    conn.close()

    return np.array(embeddings), metadata


def run_umap(embeddings: np.ndarray) -> np.ndarray:
    """Reduce high-dimensional embeddings to 2D using UMAP."""
    reducer = umap.UMAP(
        n_components=UMAP_N_COMPONENTS,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric='cosine',
        random_state=42
    )
    return reducer.fit_transform(embeddings)


def cluster_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """
    Cluster embeddings using HDBSCAN (if available).

    Returns:
        labels: cluster labels (-1 = noise, or 0 if clustering unavailable)
    """
    if not HDBSCAN_AVAILABLE:
        # Return all zeros (single cluster) if HDBSCAN unavailable
        return np.zeros(len(embeddings), dtype=int)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric='euclidean'
    )
    return clusterer.fit_predict(embeddings)


def compute_edges(embeddings: np.ndarray, coords: np.ndarray) -> List[Tuple[int, int, float]]:
    """
    Compute edges between highly similar chunks.

    Returns:
        List of (i, j, similarity) tuples
    """
    # Compute cosine similarity matrix
    sim_matrix = cosine_similarity(embeddings)

    # Find pairs above threshold
    edges = []
    n = len(embeddings)

    for i in range(n):
        for j in range(i + 1, n):
            sim = sim_matrix[i, j]
            if sim >= EDGE_SIMILARITY_THRESHOLD:
                edges.append((i, j, sim))

    # Sort by similarity (highest first) and cap
    edges.sort(key=lambda x: x[2], reverse=True)
    return edges[:MAX_EDGES]


def create_dashboard(coords: np.ndarray, labels: np.ndarray, metadata: List[Dict], edges: List[Tuple[int, int, float]]):
    """Create interactive Plotly dashboard."""

    # Color map for clusters
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    colors = ['hsl({}, 70%, 50%)'.format(i * 360 / n_clusters) for i in range(n_clusters)]
    color_map = {i: colors[i] for i in set(labels) if i != -1}
    color_map[-1] = 'hsl(0, 0%, 70%)'  # Gray for noise

    # Assign colors to nodes
    node_colors = [color_map[label] for label in labels]

    # Create scatter trace (nodes)
    node_trace = go.Scatter(
        x=coords[:, 0],
        y=coords[:, 1],
        mode='markers',
        marker=dict(
            size=NODE_SIZE,
            color=node_colors,
            opacity=NODE_OPACITY,
            line=dict(width=1, color='rgba(0,0,0,0.2)')
        ),
        hovertemplate=[
            f"<b>Chunk {m['chunk_id']}</b><br>"
            f"File: {m['file_path']}<br>"
            f"Lines: {m['line_start']}-{m['line_end']}<br>"
            f"Cluster: {labels[i]}<br>"
            f"<i>{m['content']}</i>"
            for i, m in enumerate(metadata)
        ],
        name="Memory Chunks"
    )

    # Create line traces for edges
    edge_traces = []
    for i, j, sim in edges:
        x0, y0 = coords[i]
        x1, y1 = coords[j]

        # Opacity based on similarity
        opacity = (sim - EDGE_SIMILARITY_THRESHOLD) / (1.0 - EDGE_SIMILARITY_THRESHOLD) * 0.5

        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=1, color=f'rgba(0,0,0,{opacity})'),
            hoverinfo='none',
            showlegend=False
        )
        edge_traces.append(edge_trace)

    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])

    # Layout
    n_unique_clusters = len(set(labels))
    fig.update_layout(
        title=f"OpenClaw Memory Visualization<br>"
              f"<sup>{len(metadata)} chunks • {n_unique_clusters} clusters • {len(edges)} semantic edges</sup>",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=80),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title_text=""),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title_text=""),
        plot_bgcolor='rgba(255,255,255,1)',
        paper_bgcolor='rgba(255,255,255,1)',
        font=dict(family="Arial, sans-serif", size=12)
    )

    # Save to HTML
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(OUTPUT_FILE))
    print(f"✓ Dashboard saved to {OUTPUT_FILE}")

    return fig


def main():
    print("Building memory dashboard...")

    # Step 1: Get embeddings from SQLite
    print("  → Loading embeddings...")
    embeddings, metadata = get_embeddings(DB_PATH)
    print(f"  → Loaded {len(embeddings)} chunks")

    # Step 2: UMAP for 2D projection
    print("  → Running UMAP projection...")
    coords = run_umap(embeddings)
    print(f"  → Projected to 2D: shape={coords.shape}")

    # Step 3: HDBSCAN clustering
    print("  → Clustering with HDBSCAN...")
    labels = cluster_embeddings(embeddings)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    print(f"  → Found {n_clusters} clusters, {n_noise} noise points")

    # Step 4: Compute edges (high similarity pairs)
    print("  → Computing semantic edges...")
    edges = compute_edges(embeddings, coords)
    print(f"  → Created {len(edges)} edges (similarity ≥ {EDGE_SIMILARITY_THRESHOLD})")

    # Step 5: Create dashboard
    print("  → Generating interactive dashboard...")
    create_dashboard(coords, labels, metadata, edges)

    print("\n✓ Done!")
    print(f"  Open in browser: file://{OUTPUT_FILE.absolute()}")


if __name__ == "__main__":
    main()
