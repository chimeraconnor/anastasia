#!/usr/bin/env python3
"""
Ana's Brain — Build Pipeline
=============================
Reads QMD SQLite embeddings, projects to 3D via UMAP, clusters via OPTICS,
and outputs graph_data.json for the 3D brain dashboard.

Run inside the OpenClaw container:
  python3 build_graph.py

Output:  graph_data.json  (consumed by dashboard.html)
"""

import json
import re
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

try:
    import umap as umap_module
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False

from sklearn.cluster import OPTICS
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize

# ─── Config ──────────────────────────────────────────────────────────────────

DB_PATH   = Path("/home/node/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite")
EXT_PATH  = Path("/home/node/.bun/install/global/node_modules/sqlite-vec-linux-x64/vec0.so")
OUT_DIR   = Path("/home/node/.openclaw/workspace/tools/memory-dashboard")
OUT_JSON  = OUT_DIR / "graph_data.json"

UMAP_NEIGHBORS = 12
UMAP_MIN_DIST  = 0.18

# OPTICS clustering on raw embeddings (high-dim)
OPTICS_MIN_SAMPLES  = 2
OPTICS_MAX_EPS      = 1.0    # L2 distance upper bound (on L2-normed vecs)
OPTICS_XI           = 0.03
ASSIGN_NOISE        = True   # Assign noise points to nearest cluster

# Edge: top-K nearest neighbors per node
EDGE_K         = 3
EDGE_MIN_SIM   = 0.50

# ─── Classify chunks by source ───────────────────────────────────────────────

def _classify(collection: str, path: str) -> str:
    if collection in ("memory-root-main", "memory-alt-main"):
        return "lesson"
    if collection == "memory-dir-main":
        if re.match(r"^\d{4}-\d{2}-\d{2}", path):
            return "daily"
        return "instruction"
    if collection == "sessions-main":
        return "session"
    return "other"


def _date_from(collection: str, path: str, created_at: str) -> str:
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", path)
    if m:
        return m.group(1)
    return created_at[:10] if created_at else "unknown"


def _clean_text(text: str, source_type: str) -> str:
    """Strip raw metadata, JSON blobs, and UUIDs from chunk text for human readability."""
    # Remove session UUID headers
    text = re.sub(r'^#+ Session [0-9a-f-]{36}\s*', '', text)
    # Remove "Conversation info (untrusted metadata): ```json ... ```" blocks
    text = re.sub(
        r'(?:User: )?Conversation info \(untrusted metadata\):\s*```json?\s*\{[^}]*\}\s*```',
        '', text, flags=re.DOTALL
    )
    # Remove "Sender (untrusted metadata): ```json ... ```" blocks
    text = re.sub(
        r'Sender \(untrusted metadata\):\s*```json?\s*\{[^}]*\}\s*```',
        '', text, flags=re.DOTALL
    )
    # Remove standalone JSON objects (message_id, sender_id, etc.)
    text = re.sub(r'```json?\s*\{[^}]{0,500}\}\s*```', '', text, flags=re.DOTALL)
    # Remove lone UUIDs
    text = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '', text)
    # Remove "Current time: ..." lines
    text = re.sub(r'Current time:[^\n]*\n?', '', text)
    # Remove "Return your summary as plain text..." boilerplate
    text = re.sub(r'Return your summary as plain text[^\n]*\n?', '', text)
    # Clean up multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _make_summary(text: str, title: str, source_type: str) -> str:
    """Extract a short human-readable summary from chunk text."""
    cleaned = _clean_text(text, source_type)
    if not cleaned:
        return title
    # For sessions, try to find the first substantive message
    if source_type == 'session':
        # Find first User: or Assistant: line with real content
        for pattern in [r'(?:User|Assistant):\s*(.+)', r'^(.{20,})']:
            m = re.search(pattern, cleaned, re.MULTILINE)
            if m:
                line = m.group(1).strip()
                if len(line) > 15:  # skip very short lines
                    return line[:200]
    # For other types, take first meaningful line
    for line in cleaned.split('\n'):
        line = line.strip().lstrip('#').strip()
        if len(line) > 15:
            return line[:200]
    return title


# ─── Load from QMD ───────────────────────────────────────────────────────────

def load_qmd() -> Tuple[List[Dict], np.ndarray]:
    """Pull chunks + embeddings from QMD SQLite."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"QMD database not found: {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.enable_load_extension(True)
    if EXT_PATH.exists():
        conn.load_extension(str(EXT_PATH))
    cur = conn.cursor()

    # All documents with their chunk positions
    cur.execute("""
        SELECT d.collection, d.path, d.title, d.hash, d.created_at,
               c.doc, cv.seq, cv.pos
        FROM documents d
        JOIN content c ON d.hash = c.hash
        JOIN content_vectors cv ON cv.hash = d.hash
        WHERE d.active = 1
        ORDER BY d.hash, cv.seq
    """)
    rows = cur.fetchall()

    # Group by document
    doc_info: Dict[str, Dict] = {}
    doc_seqs: Dict[str, List] = {}
    for col, path, title, hash_, created, doc, seq, pos in rows:
        if hash_ not in doc_info:
            doc_info[hash_] = dict(collection=col, path=path, title=title,
                                   hash=hash_, created_at=created, doc=doc)
            doc_seqs[hash_] = []
        doc_seqs[hash_].append((seq, pos))

    # Build chunk records with extracted text
    records: List[Dict] = []
    for hash_, info in doc_info.items():
        chunks = sorted(doc_seqs[hash_], key=lambda x: x[0])
        doc_text = info["doc"]
        stype = _classify(info["collection"], info["path"])
        date  = _date_from(info["collection"], info["path"], info["created_at"])

        for i, (seq, pos) in enumerate(chunks):
            end_pos = chunks[i+1][1] if i+1 < len(chunks) else len(doc_text)
            raw_text = doc_text[pos:end_pos].strip()
            cleaned = _clean_text(raw_text, stype)
            summary = _make_summary(raw_text, info["title"], stype)
            records.append(dict(
                hash_seq    = f"{hash_}_{seq}",
                source_type = stype,
                collection  = info["collection"],
                path        = info["path"],
                title       = info["title"],
                date        = date,
                text        = cleaned[:600] + "..." if len(cleaned) > 600 else cleaned,
                summary     = summary,
            ))

    # Load embeddings
    cur.execute("SELECT hash_seq, embedding FROM vectors_vec")
    emb_map: Dict[str, np.ndarray] = {}
    for hs, blob in cur.fetchall():
        emb_map[hs] = np.frombuffer(blob, dtype=np.float32).copy()
    conn.close()

    # Match records to embeddings
    valid = [(r, emb_map[r["hash_seq"]]) for r in records if r["hash_seq"] in emb_map]
    if not valid:
        raise ValueError("No embeddings found matching chunk records")

    records    = [v[0] for v in valid]
    embeddings = np.array([v[1] for v in valid])
    return records, embeddings


# ─── UMAP projection ─────────────────────────────────────────────────────────

def project_3d(embeddings: np.ndarray) -> np.ndarray:
    n = len(embeddings)
    if HAS_UMAP and n >= max(8, UMAP_NEIGHBORS + 1):
        nn = min(UMAP_NEIGHBORS, n - 1)
        reducer = umap_module.UMAP(
            n_components=3,
            n_neighbors=nn,
            min_dist=UMAP_MIN_DIST,
            metric="cosine",
            random_state=42,
            low_memory=True,
        )
        return reducer.fit_transform(embeddings)
    return PCA(n_components=3, random_state=42).fit_transform(embeddings)


# ─── Clustering ───────────────────────────────────────────────────────────────

def cluster_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """OPTICS on cosine-distance normalized embeddings. Returns cluster labels."""
    normed = normalize(embeddings)
    # cosine distance = 1 - cosine_sim.  OPTICS with metric precomputed is slow
    # Instead use euclidean on L2-normalized vectors (equivalent for cosine)
    clust = OPTICS(
        min_samples=OPTICS_MIN_SAMPLES,
        max_eps=OPTICS_MAX_EPS,
        xi=OPTICS_XI,
        metric="euclidean",
        cluster_method="xi",
    )
    labels = clust.fit_predict(normed)
    return labels


# ─── Edges (KNN) ─────────────────────────────────────────────────────────────

def build_edges(embeddings: np.ndarray) -> List[Dict]:
    normed = normalize(embeddings)
    sim = normed @ normed.T
    np.fill_diagonal(sim, -1.0)

    seen = set()
    edges = []
    for i in range(len(embeddings)):
        top_j = np.argsort(sim[i])[::-1][:EDGE_K]
        for j in top_j:
            s = float(sim[i, j])
            if s < EDGE_MIN_SIM:
                break
            key = (min(i, j), max(i, j))
            if key not in seen:
                seen.add(key)
                edges.append(dict(source=int(i), target=int(j), weight=round(s, 3)))
    return edges


# ─── Auto-label clusters from content ────────────────────────────────────────

def auto_label_cluster(records: List[Dict], indices: List[int]) -> str:
    """
    Heuristic label: take top keywords from chunk titles/text.
    LLM labeling happens in the cron job (stage 2).
    """
    from collections import Counter

    STOP = {"the","a","an","to","of","in","is","it","and","for","on","with",
            "that","this","was","are","be","as","at","by","from","or","not",
            "but","have","has","had","i","you","we","my","me","your","our",
            "he","she","they","them","their","its","been","will","would",
            "can","could","do","does","did","just","then","now","so","if",
            "about","up","out","what","which","when","how","all","each",
            "some","any","no","more","other","than","into","also","very",
            "here","there","where","who","mr","grey","user","assistant",
            "session","conversation","info","untrusted","metadata","sender",
            "message","label","name","username","tag","json","channel",
            "group","subject","space","guild","id","md","txt","http","https"}

    words = Counter()
    for idx in indices[:30]:  # sample up to 30 chunks
        combined = records[idx]["title"] + " " + records[idx]["text"][:300]
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_.-]{2,}", combined.lower())
        for t in tokens:
            if t not in STOP and len(t) < 30:
                words[t] += 1

    top = [w for w, _ in words.most_common(4)]
    return " / ".join(top) if top else "uncategorized"


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Building Ana's Brain data...")

    # Load
    print("  Loading QMD embeddings...")
    records, embeddings = load_qmd()
    n = len(records)
    print(f"  {n} chunks loaded")

    # Project 3D
    print("  UMAP 3D projection...")
    coords = project_3d(embeddings)
    # Normalize coords to [-80, 80] range — wide spread so nodes don't clump
    coords = (coords - coords.mean(axis=0)) / (coords.std(axis=0) + 1e-8) * 80

    # Cluster
    print("  Clustering (OPTICS)...")
    labels = cluster_embeddings(embeddings)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1))
    print(f"  {n_clusters} clusters, {n_noise} noise points")

    # Assign noise points to nearest cluster centroid
    if ASSIGN_NOISE and n_clusters > 0 and n_noise > 0:
        normed = normalize(embeddings)
        centroids = {}
        for cid in set(labels):
            if cid == -1:
                continue
            mask = labels == cid
            centroids[cid] = normed[mask].mean(axis=0)
            centroids[cid] /= np.linalg.norm(centroids[cid]) + 1e-8
        centroid_ids = sorted(centroids.keys())
        centroid_mat = np.stack([centroids[c] for c in centroid_ids])
        noise_mask = labels == -1
        noise_idx = np.where(noise_mask)[0]
        sims = normed[noise_idx] @ centroid_mat.T
        best = sims.argmax(axis=1)
        for i, nidx in enumerate(noise_idx):
            labels[nidx] = centroid_ids[best[i]]
        n_assigned = len(noise_idx)
        print(f"  Assigned {n_assigned} noise points to nearest cluster")

    # Auto-label clusters
    print("  Labeling clusters...")
    cluster_ids = sorted(set(labels))
    cluster_meta = {}
    for cid in cluster_ids:
        members = [i for i in range(n) if labels[i] == cid]
        if cid == -1:
            cluster_meta[-1] = dict(id=-1, label="unclustered", count=len(members))
        else:
            lbl = auto_label_cluster(records, members)
            cluster_meta[int(cid)] = dict(id=int(cid), label=lbl, count=len(members))

    # Build edges
    print("  Building KNN edges...")
    edges = build_edges(embeddings)
    print(f"  {len(edges)} edges")

    # Assemble nodes
    nodes = []
    for i, rec in enumerate(records):
        nodes.append(dict(
            id=i,
            x=round(float(coords[i, 0]), 2),
            y=round(float(coords[i, 1]), 2),
            z=round(float(coords[i, 2]), 2),
            cluster=int(labels[i]),
            source_type=rec["source_type"],
            title=rec["title"],
            path=rec["path"],
            date=rec["date"],
            text=rec["text"],
            summary=rec["summary"],
        ))

    # Output
    data = dict(
        generated=datetime.now().isoformat(),
        stats=dict(
            total_chunks=n,
            clusters=n_clusters,
            edges=len(edges),
            noise_points=n_noise,
        ),
        clusters=list(cluster_meta.values()),
        nodes=nodes,
        edges=edges,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    size_kb = OUT_JSON.stat().st_size // 1024
    print(f"\n  Done! {size_kb} KB -> {OUT_JSON}")


if __name__ == "__main__":
    main()
