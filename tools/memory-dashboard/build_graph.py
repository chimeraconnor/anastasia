#!/usr/bin/env python3
"""
Ana's Brain  —  Build Pipeline v2
==================================
Reads workspace MD files directly, chunks by semantic sections (## headers),
maps to QMD embeddings where available, and uses TF-IDF fallback for the rest.

This is SEPARATE from QMD's retrieval system. QMD chunks for RAG; we chunk for
visualization. Same source files, different strategy.

Run inside the OpenClaw container:
    python3 build_graph.py

Outputs:
    graph_data.json        — latest snapshot (consumed by brain.html)
    snapshots/YYYY-MM-DD.json — daily archive for history view
"""

import json
import re
import sqlite3
import shutil
from collections import Counter
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import umap as umap_module
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False

from sklearn.cluster import OPTICS
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

# ─── Config ──────────────────────────────────────────────────────────────────

# QMD database (read-only — we never write to it)
DB_PATH  = Path("/home/node/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite")
EXT_PATH = Path("/home/node/.bun/install/global/node_modules/sqlite-vec-linux-x64/vec0.so")

# Workspace root (where the agent's files live)
WORKSPACE = Path("/home/node/.openclaw/workspace")

# Output
OUT_DIR      = Path("/home/node/.openclaw/workspace/tools/memory-dashboard")
OUT_JSON     = OUT_DIR / "graph_data.json"
SNAPSHOT_DIR = OUT_DIR / "snapshots"

# Files to scan — these are Ana's accessible knowledge files
# Format: (glob_pattern, source_type, base_dir)
SCAN_SOURCES = [
    # Core identity / knowledge files
    ("MEMORY.md",      "lesson",      WORKSPACE),
    ("SOUL.md",        "identity",    WORKSPACE),
    ("IDENTITY.md",    "identity",    WORKSPACE),
    ("USER.md",        "identity",    WORKSPACE),
    ("PROJECTS.md",    "knowledge",   WORKSPACE),
    ("TOOLS.md",       "knowledge",   WORKSPACE),
    ("TODO.md",        "knowledge",   WORKSPACE),
    ("AGENTS.md",      "knowledge",   WORKSPACE),
    ("HEARTBEAT.md",   "knowledge",   WORKSPACE),
    # Daily memory notes
    ("memory/*.md",    "daily",       WORKSPACE),
    # Skills documentation
    ("skills/*/SKILL.md",   "skill",  WORKSPACE),
    ("skills/*/README.md",  "skill",  WORKSPACE),
]

# Session transcripts are stored elsewhere (QMD's session dir)
SESSION_DIR = Path("/home/node/.openclaw/agents/main/qmd/sessions")

# UMAP
UMAP_NEIGHBORS = 12
UMAP_MIN_DIST  = 0.15

# OPTICS clustering
OPTICS_MIN_SAMPLES = 2
OPTICS_MAX_EPS     = 1.0
OPTICS_XI          = 0.03
ASSIGN_NOISE       = True

# KNN edges
EDGE_K       = 3
EDGE_MIN_SIM = 0.45

# Embedding dimension (embeddinggemma uses 768)
EMBED_DIM = 768

# ─── Semantic section splitter ────────────────────────────────────────────────

def split_md_sections(text: str, filepath: str, max_depth: int = 3,
                      max_sections: int = 30) -> List[Dict]:
    """
    Split a markdown file into semantic sections based on ## and ### headers.
    Each section becomes one brain node.

    Args:
        max_depth: Maximum header depth to split on (2=##, 3=###)
        max_sections: Cap at this many sections per file.

    Returns list of dicts: {title, text, level, line_start}
    """
    lines = text.split("\n")
    sections = []
    current_title = Path(filepath).stem  # fallback title = filename
    current_level = 1
    current_lines = []
    current_start = 1

    for i, line in enumerate(lines):
        # Match ## or ### headers (not # which is the file title)
        m = re.match(r'^(#{2,' + str(max_depth) + r'})\s+(.+)', line)
        if m:
            # Save previous section if it has content
            body = "\n".join(current_lines).strip()
            if body and len(body) > 20:  # skip tiny sections
                sections.append(dict(
                    title=current_title,
                    text=body,
                    level=current_level,
                    line_start=current_start,
                ))
            # Start new section
            current_level = len(m.group(1))
            current_title = m.group(2).strip()
            current_lines = []
            current_start = i + 1
        else:
            current_lines.append(line)

    # Don't forget the last section
    body = "\n".join(current_lines).strip()
    if body and len(body) > 20:
        sections.append(dict(
            title=current_title,
            text=body,
            level=current_level,
            line_start=current_start,
        ))

    # If no sections found (file has no ## headers), treat whole file as one section
    if not sections and len(text.strip()) > 20:
        # Use the # title if present
        m = re.match(r'^#\s+(.+)', text)
        title = m.group(1).strip() if m else Path(filepath).stem
        sections.append(dict(
            title=title,
            text=text.strip(),
            level=1,
            line_start=1,
        ))

    # Cap sections per file to avoid one huge doc dominating
    if len(sections) > max_sections:
        # Keep the largest / most meaningful sections by text length
        sections.sort(key=lambda s: len(s["text"]), reverse=True)
        sections = sections[:max_sections]
        # Re-sort by line position for consistency
        sections.sort(key=lambda s: s["line_start"])

    return sections


def split_session(text: str, filepath: str) -> List[Dict]:
    """
    Split a session transcript into a single summarized node.
    Sessions are conversations — we summarize rather than split by headers.
    """
    # Clean metadata
    cleaned = _clean_session_text(text)
    if len(cleaned) < 30:
        return []

    # Extract a meaningful summary from first substantive exchange
    summary = _extract_session_summary(cleaned)
    session_id = Path(filepath).stem

    return [dict(
        title=summary[:80],
        text=cleaned[:800],
        level=1,
        line_start=1,
    )]


def _clean_session_text(text: str) -> str:
    """Strip raw metadata from session transcripts."""
    # Remove session UUID headers
    text = re.sub(r'^#+ Session [0-9a-f-]{36}\s*', '', text)
    # Remove "Conversation info (untrusted metadata): ```json {...} ```" blocks
    text = re.sub(
        r'(?:User: )?Conversation info \(untrusted metadata\):\s*```json?\s*\{[^}]*\}\s*```',
        '', text, flags=re.DOTALL
    )
    # Remove "Sender (untrusted metadata)" blocks
    text = re.sub(
        r'Sender \(untrusted metadata\):\s*```json?\s*\{[^}]*\}\s*```',
        '', text, flags=re.DOTALL
    )
    # Remove standalone JSON blocks
    text = re.sub(r'```json?\s*\{[^}]{0,500}\}\s*```', '', text, flags=re.DOTALL)
    # Remove lone UUIDs
    text = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '', text)
    # Remove "Current time:" lines
    text = re.sub(r'Current time:[^\n]*\n?', '', text)
    # Remove boilerplate
    text = re.sub(r'Return your summary as plain text[^\n]*\n?', '', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_session_summary(text: str) -> str:
    """Get first meaningful line from a cleaned session."""
    for pattern in [r'(?:Assistant|User):\s*(.{20,})', r'^(.{20,})']:
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            line = m.group(1).strip()
            # Skip lines that are just metadata remnants
            if not re.match(r'^[\s\[\(]*(cron|untrusted|metadata)', line, re.I):
                return line[:200]
    return text[:100]


# ─── Source file scanner ──────────────────────────────────────────────────────

def scan_workspace() -> List[Dict]:
    """
    Scan workspace for all MD files that form Ana's knowledge.
    Returns list of node records (one per semantic section).
    """
    records = []

    # Scan configured workspace sources
    for pattern, source_type, base_dir in SCAN_SOURCES:
        for filepath in sorted(base_dir.glob(pattern)):
            if not filepath.is_file():
                continue
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if len(text.strip()) < 30:
                continue

            rel_path = str(filepath.relative_to(WORKSPACE))
            file_date = _extract_date(rel_path, filepath)

            sections = split_md_sections(
                text, rel_path,
                # Skill docs are huge reference files — only split on ## headers
                # and cap to 15 sections to prevent them dominating the graph
                max_depth=2 if source_type == "skill" else 3,
                max_sections=15 if source_type == "skill" else 30,
            )
            for sec in sections:
                records.append(dict(
                    source_type=source_type,
                    path=rel_path,
                    title=sec["title"],
                    date=file_date,
                    text=sec["text"],
                    summary=_make_summary(sec["text"], sec["title"], source_type),
                    _raw_text=sec["text"],  # kept for embedding, stripped from output
                ))

    # Scan session transcripts
    if SESSION_DIR.exists():
        for filepath in sorted(SESSION_DIR.glob("**/*.md")):
            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if len(text.strip()) < 50:
                continue

            rel_path = f"sessions/{filepath.name}"
            file_date = _extract_date(filepath.name, filepath)

            sections = split_session(text, filepath.name)
            for sec in sections:
                records.append(dict(
                    source_type="session",
                    path=rel_path,
                    title=sec["title"],
                    date=file_date,
                    text=sec["text"][:600],
                    summary=sec["title"],
                    _raw_text=sec["text"],
                ))

    return records


def _extract_date(name: str, filepath: Path) -> str:
    """Extract date from filename or file mtime."""
    m = re.search(r'(\d{4}-\d{2}-\d{2})', name)
    if m:
        return m.group(1)
    try:
        mtime = filepath.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except Exception:
        return "unknown"


def _make_summary(text: str, title: str, source_type: str) -> str:
    """Create a short human-readable summary."""
    # For identity/knowledge files, the title is usually good
    if source_type in ("identity", "knowledge", "skill"):
        # Get first substantive line after any header
        for line in text.split("\n"):
            line = line.strip().lstrip("#").lstrip("-").strip()
            if len(line) > 20 and not line.startswith("```"):
                return line[:200]
        return title

    # For lessons, extract the lesson statement
    if source_type == "lesson":
        m = re.search(r'\*\*Lesson:\*\*\s*(.+)', text)
        if m:
            return m.group(1).strip()[:200]
        for line in text.split("\n"):
            line = line.strip().lstrip("#").strip()
            if len(line) > 20:
                return line[:200]

    # For daily notes, find the first content line
    for line in text.split("\n"):
        line = line.strip().lstrip("#").strip()
        if len(line) > 20 and not line.startswith("```"):
            return line[:200]
    return title


# ─── Embedding: QMD lookup + TF-IDF fallback ─────────────────────────────────

def load_qmd_embeddings() -> Tuple[List[str], np.ndarray]:
    """
    Load all embeddings from QMD's SQLite database.
    Returns (texts, embeddings) for building the TF-IDF bridge.
    """
    if not DB_PATH.exists():
        return [], np.array([])

    conn = sqlite3.connect(str(DB_PATH))
    conn.enable_load_extension(True)
    if EXT_PATH.exists():
        conn.load_extension(str(EXT_PATH))
    cur = conn.cursor()

    # Get all chunks with their text and embeddings
    cur.execute("""
        SELECT c.doc, cv.hash, cv.seq, cv.pos
        FROM content_vectors cv
        JOIN content c ON cv.hash = c.hash
        ORDER BY cv.hash, cv.seq
    """)
    chunk_rows = cur.fetchall()

    # Group by (hash, seq) to get text slices
    chunks_by_hash: Dict[str, List] = {}
    doc_text: Dict[str, str] = {}
    for doc, hash_, seq, pos in chunk_rows:
        doc_text[hash_] = doc
        if hash_ not in chunks_by_hash:
            chunks_by_hash[hash_] = []
        chunks_by_hash[hash_].append((seq, pos))

    # Extract chunk texts and their hash_seq keys
    chunk_texts = []
    chunk_keys = []
    for hash_, seqs in chunks_by_hash.items():
        seqs_sorted = sorted(seqs, key=lambda x: x[0])
        full_text = doc_text[hash_]
        for i, (seq, pos) in enumerate(seqs_sorted):
            end_pos = seqs_sorted[i+1][1] if i+1 < len(seqs_sorted) else len(full_text)
            text = full_text[pos:end_pos].strip()
            chunk_texts.append(text)
            chunk_keys.append(f"{hash_}_{seq}")

    # Load embeddings
    cur.execute("SELECT hash_seq, embedding FROM vectors_vec")
    emb_map = {}
    for hs, blob in cur.fetchall():
        emb_map[hs] = np.frombuffer(blob, dtype=np.float32).copy()
    conn.close()

    # Match texts to embeddings (in order)
    texts_out = []
    embs_out = []
    for text, key in zip(chunk_texts, chunk_keys):
        if key in emb_map:
            texts_out.append(text)
            embs_out.append(emb_map[key])

    if embs_out:
        return texts_out, np.array(embs_out)
    return [], np.array([])


def compute_embeddings(records: List[Dict], qmd_texts: List[str],
                       qmd_embeddings: np.ndarray) -> np.ndarray:
    """
    For each record, compute an embedding:
    1. Find best matching QMD chunk by text overlap → use its real embedding
    2. If no good match, use TF-IDF projected into QMD's embedding space

    This hybrid approach keeps QMD-embedded content positioned by deep semantic
    similarity, while placing new content reasonably via TF-IDF nearest-neighbor.
    """
    n = len(records)
    embeddings = np.zeros((n, EMBED_DIM), dtype=np.float32)
    method_counts = Counter()

    if len(qmd_texts) == 0 or len(qmd_embeddings) == 0:
        # No QMD data at all — pure TF-IDF with random projection
        print("  WARNING: No QMD embeddings found, using TF-IDF only")
        return _tfidf_fallback(records)

    # Build TF-IDF on combined corpus (QMD chunks + our records)
    all_texts = qmd_texts + [r["_raw_text"][:2000] for r in records]
    tfidf = TfidfVectorizer(
        max_features=5000,
        stop_words="english",
        sublinear_tf=True,
    )
    tfidf_matrix = tfidf.fit_transform(all_texts)

    # TF-IDF vectors for QMD chunks and our records
    qmd_tfidf = tfidf_matrix[:len(qmd_texts)]
    our_tfidf = tfidf_matrix[len(qmd_texts):]

    # For each of our records, find the best matching QMD chunk
    # Use cosine similarity between TF-IDF vectors as the matching criterion
    qmd_tfidf_normed = normalize(qmd_tfidf)
    our_tfidf_normed = normalize(our_tfidf)

    # Compute similarity matrix (our records × QMD chunks)
    # Do in batches to avoid memory issues
    BATCH = 50
    for start in range(0, n, BATCH):
        end = min(start + BATCH, n)
        batch_sim = (our_tfidf_normed[start:end] @ qmd_tfidf_normed.T).toarray()

        for i in range(end - start):
            idx = start + i
            best_qmd_idx = batch_sim[i].argmax()
            best_sim = batch_sim[i, best_qmd_idx]

            if best_sim > 0.15:  # decent text overlap
                # Use the real QMD embedding
                embeddings[idx] = qmd_embeddings[best_qmd_idx]

                # If multiple good matches, average top-3
                if best_sim > 0.3:
                    top3 = batch_sim[i].argsort()[-3:][::-1]
                    weights = batch_sim[i, top3]
                    weights = weights / (weights.sum() + 1e-8)
                    embeddings[idx] = (qmd_embeddings[top3] * weights[:, None]).sum(axis=0)
                    method_counts["qmd_multi"] += 1
                else:
                    method_counts["qmd_single"] += 1
            else:
                # No good match — use TF-IDF nearest neighbor interpolation
                # Take top-5 QMD chunks and average their embeddings weighted by similarity
                top5 = batch_sim[i].argsort()[-5:][::-1]
                weights = np.maximum(batch_sim[i, top5], 0.01)
                weights = weights / weights.sum()
                embeddings[idx] = (qmd_embeddings[top5] * weights[:, None]).sum(axis=0)
                method_counts["tfidf_interp"] += 1

    print(f"  Embedding methods: {dict(method_counts)}")
    return embeddings


def _tfidf_fallback(records: List[Dict]) -> np.ndarray:
    """Pure TF-IDF with random projection to EMBED_DIM when no QMD data exists."""
    texts = [r["_raw_text"][:2000] for r in records]
    tfidf = TfidfVectorizer(max_features=5000, stop_words="english", sublinear_tf=True)
    tfidf_matrix = tfidf.fit_transform(texts).toarray()
    # Random projection to EMBED_DIM
    rng = np.random.RandomState(42)
    proj = rng.randn(tfidf_matrix.shape[1], EMBED_DIM).astype(np.float32)
    proj /= np.linalg.norm(proj, axis=0, keepdims=True)
    return (tfidf_matrix @ proj).astype(np.float32)


# ─── 3D Projection ───────────────────────────────────────────────────────────

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
    normed = normalize(embeddings)
    clust = OPTICS(
        min_samples=OPTICS_MIN_SAMPLES,
        max_eps=OPTICS_MAX_EPS,
        xi=OPTICS_XI,
        metric="euclidean",
        cluster_method="xi",
    )
    labels = clust.fit_predict(normed)
    return labels


def assign_noise_to_clusters(labels: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    """Assign noise points (-1) to nearest cluster centroid."""
    labels = labels.copy()
    cluster_ids = sorted(set(labels) - {-1})
    if not cluster_ids:
        return labels

    normed = normalize(embeddings)
    centroids = {}
    for cid in cluster_ids:
        mask = labels == cid
        c = normed[mask].mean(axis=0)
        centroids[cid] = c / (np.linalg.norm(c) + 1e-8)

    centroid_mat = np.stack([centroids[c] for c in cluster_ids])
    noise_idx = np.where(labels == -1)[0]
    if len(noise_idx) == 0:
        return labels

    sims = normed[noise_idx] @ centroid_mat.T
    best = sims.argmax(axis=1)
    for i, nidx in enumerate(noise_idx):
        labels[nidx] = cluster_ids[best[i]]

    return labels


# ─── KNN Edges ────────────────────────────────────────────────────────────────

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


# ─── Cluster labeling ────────────────────────────────────────────────────────

STOP = frozenset({
    "the","a","an","to","of","in","is","it","and","for","on","with",
    "that","this","was","are","be","as","at","by","from","or","not",
    "but","have","has","had","i","you","we","my","me","your","our",
    "he","she","they","them","their","its","been","will","would",
    "can","could","do","does","did","just","then","now","so","if",
    "about","up","out","what","which","when","how","all","each",
    "some","any","no","more","other","than","into","also","very",
    "here","there","where","who","don","should","use","used","using",
    "like","make","made","set","got","get","new","one","know",
    "user","assistant","session","message","json","http","https",
})

def auto_label_cluster(records: List[Dict], indices: List[int]) -> str:
    words = Counter()
    for idx in indices[:30]:
        combined = records[idx]["title"] + " " + records[idx]["text"][:300]
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_.-]{2,}", combined.lower())
        for t in tokens:
            if t not in STOP and len(t) < 25:
                words[t] += 1
    top = [w for w, _ in words.most_common(4)]
    return " / ".join(top) if top else "uncategorized"


# ─── Snapshot management ─────────────────────────────────────────────────────

def save_snapshot(data: Dict) -> Path:
    """Save a dated snapshot and return its path."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    snap_path = SNAPSHOT_DIR / f"{today}.json"
    snap_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return snap_path


def list_snapshots() -> List[str]:
    """List available snapshot dates."""
    if not SNAPSHOT_DIR.exists():
        return []
    dates = []
    for f in sorted(SNAPSHOT_DIR.glob("*.json")):
        dates.append(f.stem)  # YYYY-MM-DD
    return dates


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Ana's Brain — Build Pipeline v2")
    print("=" * 60)

    # 1. Scan workspace files
    print("\n[1/6] Scanning workspace files...")
    records = scan_workspace()
    n = len(records)
    src_counts = Counter(r["source_type"] for r in records)
    print(f"  {n} sections found:")
    for k, v in sorted(src_counts.items()):
        print(f"    {k}: {v}")

    if n == 0:
        print("  ERROR: No sections found!")
        return

    # 2. Load QMD embeddings (read-only)
    print("\n[2/6] Loading QMD embeddings (read-only)...")
    qmd_texts, qmd_embeddings = load_qmd_embeddings()
    print(f"  {len(qmd_texts)} QMD chunks with embeddings")

    # 3. Compute embeddings for our sections
    print("\n[3/6] Computing embeddings (QMD match + TF-IDF fallback)...")
    embeddings = compute_embeddings(records, qmd_texts, qmd_embeddings)

    # 4. UMAP 3D projection
    print("\n[4/6] UMAP 3D projection...")
    coords = project_3d(embeddings)
    # Normalize to [-80, 80] for good spatial spread
    coords = (coords - coords.mean(axis=0)) / (coords.std(axis=0) + 1e-8) * 80

    # 5. Clustering
    print("\n[5/6] Clustering (OPTICS)...")
    labels = cluster_embeddings(embeddings)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1))
    print(f"  {n_clusters} clusters, {n_noise} noise points")

    if ASSIGN_NOISE and n_clusters > 0 and n_noise > 0:
        labels = assign_noise_to_clusters(labels, embeddings)
        print(f"  Assigned {n_noise} noise points to nearest cluster")

    # Label clusters
    cluster_ids = sorted(set(labels))
    cluster_meta = []
    for cid in cluster_ids:
        members = [i for i in range(n) if labels[i] == cid]
        if cid == -1:
            cluster_meta.append(dict(id=-1, label="unclustered", count=len(members)))
        else:
            lbl = auto_label_cluster(records, members)
            cluster_meta.append(dict(id=int(cid), label=lbl, count=len(members)))

    # 6. Build edges
    print("\n[6/6] Building KNN edges...")
    edges = build_edges(embeddings)
    print(f"  {len(edges)} edges")

    # Assemble nodes (strip _raw_text from output)
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
            text=rec["text"][:600],
            summary=rec["summary"][:200],
        ))

    # Build output
    snapshots = list_snapshots()
    data = dict(
        generated=datetime.now().isoformat(),
        version=2,
        stats=dict(
            total_nodes=n,
            clusters=n_clusters,
            edges=len(edges),
            sources=dict(src_counts),
        ),
        available_snapshots=snapshots,
        clusters=cluster_meta,
        nodes=nodes,
        edges=edges,
    )

    # Write main output
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    size_kb = OUT_JSON.stat().st_size // 1024

    # Save daily snapshot
    snap_path = save_snapshot(data)

    print(f"\n{'=' * 60}")
    print(f"  Done! {n} nodes, {n_clusters} clusters, {len(edges)} edges")
    print(f"  {size_kb} KB -> {OUT_JSON}")
    print(f"  Snapshot: {snap_path.name}")
    print(f"  Snapshots available: {len(snapshots) + 1}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
