#!/usr/bin/env python3
"""
Memory Dashboard - Visualize OpenClaw memory embeddings as an interactive 2D graph.

Uses QMD backend with sqlite-vec extension.
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

# Configuration
QMD_DB_PATH = Path.home() / ".openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite"
VEC0_EXTENSION = Path("/home/node/.bun/install/global/node_modules/sqlite-vec-linux-x64/vec0.so")
OUTPUT_DIR = Path.home() / ".openclaw/workspace/tools/memory-dashboard"
OUTPUT_FILE = OUTPUT_DIR / "dashboard.html"

# UMAP Settings
UMAP_N_COMPONENTS = 2
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.1

# Edge Settings (similarity threshold for drawing edges)
EDGE_SIMILARITY_THRESHOLD = 0.75  # Only show edges for very similar chunks
MAX_EDGES = 100  # Cap to avoid clutter

# Node Size
NODE_SIZE = 12
NODE_OPACITY = 0.8


def get_qmd_embeddings(db_path: Path) -> Tuple[np.ndarray, List[Dict]]:
    """
    Query QMD SQLite for chunk embeddings and metadata.

    Returns:
        embeddings: numpy array of shape (n_chunks, embedding_dim)
        metadata: list of dicts with chunk_id, file_path, content, etc.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"QMD database not found: {db_path}")

    if not VEC0_EXTENSION.exists():
        raise FileNotFoundError(f"sqlite-vec extension not found: {VEC0_EXTENSION}")

    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    conn.load_extension(str(VEC0_EXTENSION.absolute()))
    cursor = conn.cursor()

    # Query: Join content (text) + documents (file path) + vectors_vec (embeddings)
    # vectors_vec stores: hash_seq (hash:seq), embedding (float[768] as bytes)
    query = """
        SELECT
            c.hash,
            c.doc,
            d.path,
            d.title,
            v.hash_seq,
            v.embedding
        FROM content c
        LEFT JOIN documents d ON c.hash = d.hash
        LEFT JOIN vectors_vec v ON c.hash = substr(v.hash_seq, 1, 64)
        WHERE v.embedding IS NOT NULL
        ORDER BY v.hash_seq
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    if not rows:
        raise ValueError("No embeddings found in QMD database")

    embeddings = []
    metadata = []

    for row in rows:
        hash_val, doc, path, title, hash_seq, embedding_bytes = row

        # Parse embedding from bytes (float32 array, 768 dims)
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

        if len(embedding) == 0:
            continue

        embeddings.append(embedding)
        metadata.append({
            "chunk_id": hash_seq,
            "hash": hash_val,
            "file_path": path or "unknown",
            "title": title or path or "Untitled",
            "content": doc[:300] + "..." if len(doc) > 300 else doc,
        })

    conn.close()

    if not embeddings:
        raise ValueError("No valid embeddings found in QMD database")

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


def create_dashboard(coords: np.ndarray, metadata: List[Dict], edges: List[Tuple[int, int, float]]):
    """Create interactive Plotly dashboard."""

    # Color by file path (group similar files)
    file_paths = [m['file_path'] for m in metadata]
    unique_files = list(set(file_paths))

    # Generate colors for each unique file
    colors = []
    for i, fp in enumerate(file_paths):
        # Use hash of file path for consistent color
        color_idx = hash(fp) % len(unique_files)
        # HSL colors: varying hue, saturation 70%, lightness 50%
        hue = (color_idx * 360 / len(unique_files)) if len(unique_files) > 0 else 0
        colors.append(f'hsl({hue}, 70%, 50%)')

    # Create scatter trace (nodes)
    node_trace = go.Scatter(
        x=coords[:, 0],
        y=coords[:, 1],
        mode='markers',
        marker=dict(
            size=NODE_SIZE,
            color=colors,
            opacity=NODE_OPACITY,
            line=dict(width=1, color='rgba(0,0,0,0.2)')
        ),
        hovertemplate=[
            f"<b>{m['title']}</b><br>"
            f"File: {m['file_path']}<br>"
            f"Chunk: {m['chunk_id']}<br>"
            f"<i>{m['content']}</i>"
            for m in metadata
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
    unique_file_count = len(set(m['file_path'] for m in metadata))
    fig.update_layout(
        title=f"OpenClaw Memory Visualization (QMD)<br>"
              f"<sup>{len(metadata)} chunks from {unique_file_count} files • {len(edges)} semantic edges</sup>",
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
    print("Building memory dashboard from QMD...")

    # Step 1: Get embeddings from QMD SQLite
    print("  → Loading embeddings from QMD...")
    embeddings, metadata = get_qmd_embeddings(QMD_DB_PATH)
    print(f"  → Loaded {len(embeddings)} chunks")

    # Step 2: UMAP for 2D projection
    print("  → Running UMAP projection...")
    coords = run_umap(embeddings)
    print(f"  → Projected to 2D: shape={coords.shape}")

    # Step 3: Compute edges (high similarity pairs)
    print("  → Computing semantic edges...")
    edges = compute_edges(embeddings, coords)
    print(f"  → Created {len(edges)} edges (similarity ≥ {EDGE_SIMILARITY_THRESHOLD})")

    # Step 4: Create dashboard
    print("  → Generating interactive dashboard...")
    create_dashboard(coords, metadata, edges)

    print("\n✓ Done!")
    print(f"  Open in browser: file://{OUTPUT_FILE.absolute()}")


if __name__ == "__main__":
    main()
