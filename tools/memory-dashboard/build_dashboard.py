#!/usr/bin/env python3
"""
NOTE: This file is replaced by the new build pipeline.
The old Plotly dashboard is superseded by the 3D brain viz.
See build_graph.py for the current pipeline.
"""
# OLD CODE BELOW — kept for reference, not executed.
_OLD = True
"""
Ana's Memory Dashboard (DEPRECATED)
======================
TensorBoard Projector + GraphRAG-style visualization of everything the agent
knows about you, sourced directly from the QMD embedding store.

Views:
  * 3D Projector  — UMAP 3D scatter, search+highlight, click for full text
  * Knowledge Graph — UMAP 2D + semantic edges, GraphRAG style
  * Timeline       — memories plotted on a date axis by category

Usage:
  python3 build_dashboard.py
  python3 -m http.server 7777 --directory /home/node/.openclaw/workspace/tools/memory-dashboard
  Open: http://localhost:7777/dashboard.html
"""

import json
import re
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from sklearn.decomposition import PCA

try:
    import umap as umap_module
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False
    print("WARNING: umap-learn not found, falling back to PCA")

# ─── Config ──────────────────────────────────────────────────────────────────

DB_PATH  = Path("/home/node/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite")
EXT_PATH = Path("/home/node/.bun/install/global/node_modules/sqlite-vec-linux-x64/vec0.so")
OUTPUT   = Path("/home/node/.openclaw/workspace/tools/memory-dashboard/dashboard.html")

UMAP_NEIGHBORS = 10
UMAP_MIN_DIST  = 0.12
EDGE_THRESHOLD = 0.68
EDGES_PER_NODE = 4

TYPE_COLORS = {
    "lesson":      "#FF6B6B",
    "daily":       "#45B7D1",
    "instruction": "#96CEB4",
    "session":     "#7777AA",
}
TYPE_SIZES = {
    "lesson":      13,
    "daily":        9,
    "instruction":  9,
    "session":      5,
}
TYPE_LABELS = {
    "lesson":      "Lessons",
    "daily":       "Daily Notes",
    "instruction": "Instructions",
    "session":     "Sessions",
}

DARK = dict(
    paper_bgcolor="#0d0d14",
    plot_bgcolor ="#0d0d14",
    font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif",
              color="#b0b0cc", size=11),
    margin=dict(l=4, r=4, t=36, b=4),
    showlegend=True,
    legend=dict(
        x=0.01, y=0.99,
        bgcolor="rgba(25,25,40,0.85)",
        bordercolor="rgba(180,180,220,0.15)",
        borderwidth=1,
        font=dict(size=11),
    ),
    modebar=dict(
        bgcolor="rgba(0,0,0,0)",
        color="#666688",
        activecolor="#aaaadd",
    ),
)


# ─── Data loading ─────────────────────────────────────────────────────────────

def _classify(collection: str, path: str) -> str:
    if collection in ("memory-root-main", "memory-alt-main"):
        return "lesson"
    if collection == "memory-dir-main":
        return "daily" if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", path) else "instruction"
    if collection == "sessions-main":
        return "session"
    return "instruction"

def _date(collection: str, path: str, created_at: str) -> str:
    m = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", path)
    if m:
        return m.group(1)
    return created_at[:10] if created_at else "unknown"

def load_data() -> Tuple[List[Dict], np.ndarray]:
    """
    Pull chunk text + embeddings from QMD SQLite.
    Uses content_vectors.pos to extract proper per-chunk text from the full doc.
    Returns (records, embeddings) where records[i] corresponds to embeddings[i].
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"QMD database not found: {DB_PATH}")
    if not EXT_PATH.exists():
        raise FileNotFoundError(f"sqlite-vec extension not found: {EXT_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.enable_load_extension(True)
    conn.load_extension(str(EXT_PATH))
    cur = conn.cursor()

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

    doc_info: Dict[str, Dict] = {}
    doc_seqs: Dict[str, List] = {}
    for collection, path, title, hash_, created_at, doc, seq, pos in rows:
        if hash_ not in doc_info:
            doc_info[hash_] = dict(
                collection=collection, path=path, title=title,
                hash=hash_, created_at=created_at, doc=doc
            )
            doc_seqs[hash_] = []
        doc_seqs[hash_].append((seq, pos))

    chunk_records: List[Dict] = []
    for hash_, info in doc_info.items():
        chunks = sorted(doc_seqs[hash_], key=lambda x: x[0])
        doc_text = info["doc"]
        stype = _classify(info["collection"], info["path"])
        date  = _date(info["collection"], info["path"], info["created_at"])

        for i, (seq, pos) in enumerate(chunks):
            next_pos = chunks[i + 1][1] if i + 1 < len(chunks) else len(doc_text)
            chunk_text = doc_text[pos:next_pos].strip()
            chunk_records.append(dict(
                hash_seq    = f"{hash_}_{seq}",
                hash        = hash_,
                seq         = seq,
                source_type = stype,
                collection  = info["collection"],
                path        = info["path"],
                title       = info["title"],
                date        = date,
                text        = chunk_text,
                text_short  = (chunk_text[:600] + "\u2026") if len(chunk_text) > 600 else chunk_text,
            ))

    cur.execute("SELECT hash_seq, embedding FROM vectors_vec")
    emb_map: Dict[str, np.ndarray] = {}
    for hs, emb_bytes in cur.fetchall():
        emb_map[hs] = np.frombuffer(emb_bytes, dtype=np.float32).copy()
    conn.close()

    valid = [(r, emb_map[r["hash_seq"]]) for r in chunk_records if r["hash_seq"] in emb_map]
    if not valid:
        raise ValueError("No embeddings matched chunk records. Schema may have changed.")

    records   = [v[0] for v in valid]
    embeddings = np.array([v[1] for v in valid])
    print(f"  -> {len(records)} chunks from {len(doc_info)} documents")
    return records, embeddings

# ─── Projection ───────────────────────────────────────────────────────────────

def project(embeddings: np.ndarray, n_components: int) -> np.ndarray:
    n = len(embeddings)
    if HAS_UMAP and n >= max(10, UMAP_NEIGHBORS + 1):
        nn = min(UMAP_NEIGHBORS, n - 1)
        reducer = umap_module.UMAP(
            n_components=n_components,
            n_neighbors=nn,
            min_dist=UMAP_MIN_DIST,
            metric="cosine",
            random_state=42,
            low_memory=True,
        )
        return reducer.fit_transform(embeddings)
    pca = PCA(n_components=n_components, random_state=42)
    return pca.fit_transform(embeddings)

# ─── Edges ────────────────────────────────────────────────────────────────────

def compute_edges(embeddings: np.ndarray) -> List[Dict]:
    """Top-K similar neighbours per node, deduped."""
    norms  = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / (norms + 1e-10)
    sim    = normed @ normed.T
    np.fill_diagonal(sim, -1.0)

    seen  = set()
    edges = []
    for i in range(len(embeddings)):
        top = np.argsort(sim[i])[::-1][:EDGES_PER_NODE]
        for j in top:
            if float(sim[i, j]) < EDGE_THRESHOLD:
                break
            key = (min(i, j), max(i, j))
            if key not in seen:
                seen.add(key)
                edges.append(dict(source=i, target=j, weight=float(sim[i, j])))
    return edges

# ─── Plotly figures ───────────────────────────────────────────────────────────

def _axis3d():
    return dict(showgrid=False, zeroline=False, showticklabels=False,
                showspikes=False, title_text="",
                backgroundcolor="#0d0d14", gridcolor="rgba(100,100,140,0.05)")

def fig_projector_3d(coords: np.ndarray, records: List[Dict]) -> go.Figure:
    traces = []
    for stype in ["lesson", "daily", "instruction", "session"]:
        idx = [i for i, r in enumerate(records) if r["source_type"] == stype]
        if not idx:
            continue
        pts  = coords[idx]
        recs = [records[i] for i in idx]
        traces.append(go.Scatter3d(
            x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
            mode="markers",
            name=TYPE_LABELS[stype],
            marker=dict(
                size=TYPE_SIZES[stype],
                color=TYPE_COLORS[stype],
                opacity=0.88 if stype != "session" else 0.45,
                line=dict(width=0),
            ),
            customdata=idx,
            text=[r["title"][:70] for r in recs],
            meta=[[r["date"], r["path"]] for r in recs],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "<span style='color:#888'>%{meta[1]}</span><br>"
                "Date: %{meta[0]}"
                "<extra></extra>"
            ),
        ))
    fig = go.Figure(data=traces)
    fig.update_layout(
        **DARK,
        title=dict(text="3D Memory Projector", font=dict(size=13, color="#9999cc")),
        scene=dict(
            bgcolor="#0d0d14",
            xaxis=_axis3d(), yaxis=_axis3d(), zaxis=_axis3d(),
        ),
        uirevision="projector",
    )
    return fig


def fig_knowledge_graph(coords: np.ndarray, records: List[Dict], edges: List[Dict]) -> go.Figure:
    traces = []
    ex, ey = [], []
    for e in edges:
        i, j = e["source"], e["target"]
        if records[i]["source_type"] == "session" and records[j]["source_type"] == "session":
            continue
        ex += [coords[i, 0], coords[j, 0], None]
        ey += [coords[i, 1], coords[j, 1], None]
    if ex:
        traces.append(go.Scatter(
            x=ex, y=ey, mode="lines",
            line=dict(width=1, color="rgba(140,140,200,0.18)"),
            hoverinfo="none", showlegend=False,
        ))
    for stype in ["session", "instruction", "daily", "lesson"]:
        idx  = [i for i, r in enumerate(records) if r["source_type"] == stype]
        if not idx:
            continue
        pts  = coords[idx]
        recs = [records[i] for i in idx]
        traces.append(go.Scatter(
            x=pts[:, 0], y=pts[:, 1],
            mode="markers",
            name=TYPE_LABELS[stype],
            marker=dict(
                size=TYPE_SIZES[stype],
                color=TYPE_COLORS[stype],
                opacity=0.88 if stype != "session" else 0.38,
                line=dict(width=1, color="rgba(0,0,0,0.25)"),
            ),
            customdata=idx,
            text=[r["title"][:70] for r in recs],
            meta=[f"{r['date']} \u00b7 {r['path']}" for r in recs],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "<span style='color:#888'>%{meta}</span>"
                "<extra></extra>"
            ),
        ))
    fig = go.Figure(data=traces)
    fig.update_layout(
        **DARK,
        title=dict(text="Knowledge Graph  (UMAP 2D + semantic edges)", font=dict(size=13, color="#9999cc")),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        hovermode="closest",
        uirevision="graph",
    )
    return fig


def fig_timeline(records: List[Dict]) -> go.Figure:
    type_y = {"lesson": 3.0, "daily": 2.0, "instruction": 1.0, "session": 0.0}
    traces = []
    rng = random.Random(42)
    for stype in ["lesson", "daily", "instruction", "session"]:
        idx  = [i for i, r in enumerate(records) if r["source_type"] == stype]
        if not idx:
            continue
        recs  = [records[i] for i in idx]
        dates = []
        for r in recs:
            try:
                dates.append(datetime.strptime(r["date"], "%Y-%m-%d"))
            except Exception:
                dates.append(datetime.now())
        jitter = 0.28 if stype == "session" else 0.12
        ys = [type_y[stype] + rng.uniform(-jitter, jitter) for _ in idx]
        traces.append(go.Scatter(
            x=dates, y=ys, mode="markers",
            name=TYPE_LABELS[stype],
            marker=dict(
                size=TYPE_SIZES[stype] + 2,
                color=TYPE_COLORS[stype],
                opacity=0.88 if stype != "session" else 0.55,
                line=dict(width=1, color="rgba(0,0,0,0.2)"),
            ),
            customdata=idx,
            text=[r["title"][:70] for r in recs],
            hovertemplate="<b>%{text}</b><br>Date: %{x|%Y-%m-%d}<extra></extra>",
        ))
    fig = go.Figure(data=traces)
    fig.update_layout(
        **DARK,
        title=dict(text="Memory Timeline", font=dict(size=13, color="#9999cc")),
        xaxis=dict(title="Date", showgrid=True, gridcolor="rgba(100,100,140,0.12)", zeroline=False),
        yaxis=dict(
            tickmode="array", tickvals=[0, 1, 2, 3],
            ticktext=["Sessions", "Instructions", "Daily Notes", "Lessons"],
            showgrid=True, gridcolor="rgba(100,100,140,0.12)",
            zeroline=False, range=[-0.6, 3.6],
        ),
        hovermode="closest",
        uirevision="timeline",
    )
    return fig

# ─── HTML generation ──────────────────────────────────────────────────────────

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:      #0d0d14; --sidebar: #13131e; --panel: #1a1a2a;
  --border:  rgba(180,180,240,0.09); --accent: #7b7fff;
  --text:    #c0c0d8; --text-dim: #666688;
  --lesson:  #FF6B6B; --daily: #45B7D1; --instr: #96CEB4; --session: #7777AA;
}
html,body { height:100%; background:var(--bg); color:var(--text);
  font-family:system-ui,-apple-system,'Segoe UI',sans-serif; font-size:13px; }
#layout { display:flex; height:100vh; overflow:hidden; }
#sidebar { width:280px; min-width:240px; background:var(--sidebar);
  border-right:1px solid var(--border); display:flex; flex-direction:column; overflow:hidden; }
#sidebar-header { padding:16px; border-bottom:1px solid var(--border);
  display:flex; align-items:center; gap:10px; }
.logo { font-size:22px; }
.agent-name { font-size:15px; font-weight:600; color:#e0e0f0; letter-spacing:.02em; }
.agent-sub  { font-size:10px; color:var(--text-dim); margin-top:1px; }
#sidebar-content { flex:1; overflow-y:auto; padding:12px;
  display:flex; flex-direction:column; gap:12px; }
.section-label { font-size:10px; font-weight:600; text-transform:uppercase;
  letter-spacing:.08em; color:var(--text-dim); margin-bottom:6px; }
#search { width:100%; padding:8px 10px; background:var(--panel);
  border:1px solid var(--border); border-radius:6px; color:var(--text);
  font-size:12px; outline:none; transition:border-color .15s; }
#search:focus { border-color:var(--accent); }
#search::placeholder { color:var(--text-dim); }
.filter-item { display:flex; align-items:center; gap:8px; padding:5px 0;
  cursor:pointer; user-select:none; border-radius:4px; }
.filter-item:hover { background:rgba(255,255,255,.03); }
.filter-item input { cursor:pointer; accent-color:var(--accent); }
.dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.filter-count { margin-left:auto; color:var(--text-dim); font-size:11px; }
#stats-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
.stat-card { background:var(--panel); border:1px solid var(--border);
  border-radius:6px; padding:8px 10px; }
.stat-val { font-size:19px; font-weight:700; color:#e0e0f8; }
.stat-label { font-size:10px; color:var(--text-dim); margin-top:2px; }
#detail-panel { background:var(--panel); border:1px solid var(--border);
  border-radius:8px; padding:12px; display:none; }
#detail-panel.visible { display:block; }
#detail-title { font-size:13px; font-weight:600; color:#e0e0f8; margin-bottom:6px; line-height:1.4; }
.detail-meta { font-size:11px; color:var(--text-dim); margin-bottom:3px; }
.detail-badge { display:inline-block; padding:2px 7px; border-radius:4px;
  font-size:10px; font-weight:600; margin-bottom:8px;
  text-transform:uppercase; letter-spacing:.05em; }
#detail-text { font-size:11px; line-height:1.6; color:var(--text);
  max-height:260px; overflow-y:auto;
  border-top:1px solid var(--border); padding-top:8px; margin-top:8px;
  white-space:pre-wrap; word-break:break-word; }
#detail-text::-webkit-scrollbar { width:4px; }
#detail-text::-webkit-scrollbar-thumb { background:rgba(150,150,200,.3); }
.gen-ts { font-size:10px; color:var(--text-dim); text-align:center; padding:8px 0; }
#main { flex:1; display:flex; flex-direction:column; overflow:hidden; }
#tab-bar { display:flex; gap:2px; padding:10px 12px 0;
  border-bottom:1px solid var(--border); background:var(--sidebar); flex-shrink:0; }
.tab { padding:7px 18px; background:transparent; border:none;
  border-bottom:2px solid transparent; color:var(--text-dim);
  font-size:12px; font-weight:500; cursor:pointer; border-radius:4px 4px 0 0;
  transition:color .12s,border-color .12s; }
.tab:hover { color:var(--text); }
.tab.active { color:#c0c0ff; border-bottom-color:var(--accent); }
#tab-content { flex:1; position:relative; overflow:hidden; }
.tab-panel { position:absolute; inset:0; display:none; }
.tab-panel.active { display:block; }
.tab-panel > div { width:100% !important; height:100% !important; }
#sidebar-content::-webkit-scrollbar { width:4px; }
#sidebar-content::-webkit-scrollbar-thumb { background:rgba(150,150,200,.2); }
"""

def build_html(
    fig_3d: go.Figure,
    fig_g2d: go.Figure,
    fig_tl:  go.Figure,
    records: List[Dict],
    edges:   List[Dict],
) -> str:
    fig3d_json = fig_3d.to_json()
    figg_json  = fig_g2d.to_json()
    figtl_json = fig_tl.to_json()

    nodes_json = json.dumps([
        dict(i=i, source_type=r["source_type"], title=r["title"],
             path=r["path"], date=r["date"], text=r["text_short"],
             collection=r["collection"])
        for i, r in enumerate(records)
    ], ensure_ascii=False)

    counts = {t: sum(1 for r in records if r["source_type"] == t) for t in TYPE_LABELS}
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    from plotly.offline import get_plotlyjs
    plotly_bundle = get_plotlyjs()

    # JS block — note {{ }} to escape Python f-string braces
    js = f"""
const NODES = {nodes_json};
const FIG3D  = {fig3d_json};
const FIGG   = {figg_json};
const FIGTL  = {figtl_json};
const TYPE_COLORS = {{lesson:'#FF6B6B',daily:'#45B7D1',instruction:'#96CEB4',session:'#7777AA'}};
const TYPE_LABEL  = {{lesson:'Lesson',daily:'Daily Note',instruction:'Instruction',session:'Session'}};

const CFG = {{responsive:true,displayModeBar:true,scrollZoom:true,
             modeBarButtonsToRemove:['toImage','sendDataToCloud']}};
Plotly.newPlot('plot-projector', FIG3D.data,  FIG3D.layout,  CFG);
Plotly.newPlot('plot-graph',     FIGG.data,   FIGG.layout,   CFG);
Plotly.newPlot('plot-timeline',  FIGTL.data,  FIGTL.layout,  CFG);

const PLOTS = {{projector:'plot-projector',graph:'plot-graph',timeline:'plot-timeline'}};
let activeTab = 'projector';
document.querySelectorAll('.tab').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const tab = btn.dataset.tab;
    if (tab === activeTab) return;
    activeTab = tab;
    document.querySelectorAll('.tab').forEach(b => b.classList.toggle('active', b.dataset.tab===tab));
    document.querySelectorAll('.tab-panel').forEach(p => {{
      p.classList.toggle('active', p.id.replace('panel-','')===tab);
    }});
    setTimeout(() => Plotly.Plots.resize(PLOTS[tab]), 30);
  }});
}});
window.addEventListener('resize', () => Object.values(PLOTS).forEach(Plotly.Plots.resize));

function showDetail(nodeIdx) {{
  const n = NODES[nodeIdx]; if (!n) return;
  const panel = document.getElementById('detail-panel');
  const badge = document.getElementById('detail-badge');
  badge.textContent = TYPE_LABEL[n.source_type] || n.source_type;
  badge.style.background = (TYPE_COLORS[n.source_type]||'#888')+'33';
  badge.style.color = TYPE_COLORS[n.source_type]||'#888';
  document.getElementById('detail-title').textContent = n.title;
  document.getElementById('detail-file').textContent  = '📁 ' + n.path;
  document.getElementById('detail-date').textContent  = '📅 ' + n.date;
  document.getElementById('detail-text').textContent  = n.text;
  panel.classList.add('visible');
}}
function wireClick(plotId) {{
  document.getElementById(plotId).on('plotly_click', data => {{
    if (!data||!data.points||!data.points.length) return;
    const pt = data.points[0];
    const idx = Array.isArray(pt.customdata) ? pt.customdata[0] : pt.customdata;
    if (idx != null) showDetail(idx);
  }});
}}
['plot-projector','plot-graph','plot-timeline'].forEach(wireClick);

function makeTraceIndex(figData) {{
  return figData.map(trace => (trace.customdata||[]).map(v => Array.isArray(v)?v[0]:v));
}}
const idx3d = makeTraceIndex(FIG3D.data);
const idxG  = makeTraceIndex(FIGG.data);
const idxTl = makeTraceIndex(FIGTL.data);

function applySearch(q) {{
  [['plot-projector',idx3d],['plot-graph',idxG],['plot-timeline',idxTl]].forEach(([pid,tidx]) => {{
    tidx.forEach((nodeIds, ti) => {{
      if (!nodeIds.length) return;
      const ops = nodeIds.map(ni => {{
        if (!q) return undefined;
        if (ni==null) return 0.06;
        const n = NODES[ni];
        if (!n) return 0.06;
        return (n.title.toLowerCase().includes(q)||n.text.toLowerCase().includes(q))
          ? (n.source_type==='session'?0.85:0.95) : 0.06;
      }});
      if (ops.some(v => v !== undefined))
        Plotly.restyle(pid, {{'marker.opacity': [ops]}}, [ti]);
    }});
  }});
}}
let _st; document.getElementById('search').addEventListener('input', e => {{
  clearTimeout(_st); _st = setTimeout(() => applySearch(e.target.value.trim().toLowerCase()), 180);
}});

function typeTraceMap(figData) {{
  const map = {{}};
  figData.forEach((trace, ti) => {{
    const entry = Object.entries(TYPE_LABEL).find(([k,v]) => trace.name&&trace.name.toLowerCase().includes(v.toLowerCase()));
    if (entry) {{ if (!map[entry[0]]) map[entry[0]]=[]; map[entry[0]].push(ti); }}
  }});
  return map;
}}
const map3d = typeTraceMap(FIG3D.data);
const mapG  = typeTraceMap(FIGG.data);
const mapTl = typeTraceMap(FIGTL.data);
document.querySelectorAll('.filter-item input').forEach(cb => {{
  cb.addEventListener('change', () => {{
    const vis = cb.checked ? true : 'legendonly';
    [[map3d,'plot-projector'],[mapG,'plot-graph'],[mapTl,'plot-timeline']].forEach(([map,pid]) => {{
      (map[cb.dataset.type]||[]).forEach(ti => Plotly.restyle(pid, {{visible:vis}}, [ti]));
    }});
  }});
}});
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Ana's Memory Dashboard</title>
<script>{plotly_bundle}</script>
<style>{CSS}</style>
</head>
<body>
<div id="layout">
  <div id="sidebar">
    <div id="sidebar-header">
      <span class="logo">🦞</span>
      <div><div class="agent-name">Ana's Memory</div>
      <div class="agent-sub">OpenClaw &middot; QMD backend</div></div>
    </div>
    <div id="sidebar-content">
      <div>
        <div class="section-label">Overview</div>
        <div id="stats-grid">
          <div class="stat-card"><div class="stat-val">{len(records)}</div><div class="stat-label">Chunks indexed</div></div>
          <div class="stat-card"><div class="stat-val">{len(edges)}</div><div class="stat-label">Semantic edges</div></div>
          <div class="stat-card"><div class="stat-val" style="color:var(--lesson)">{counts.get('lesson',0)}</div><div class="stat-label">Lessons learned</div></div>
          <div class="stat-card"><div class="stat-val" style="color:var(--daily)">{counts.get('daily',0)}</div><div class="stat-label">Daily entries</div></div>
        </div>
      </div>
      <div><div class="section-label">Search</div>
        <input id="search" type="text" placeholder="Filter by title or text&hellip;" autocomplete="off" /></div>
      <div>
        <div class="section-label">Sources</div>
        <label class="filter-item"><input type="checkbox" data-type="lesson" checked>
          <span class="dot" style="background:var(--lesson)"></span> Lessons
          <span class="filter-count">{counts.get('lesson',0)}</span></label>
        <label class="filter-item"><input type="checkbox" data-type="daily" checked>
          <span class="dot" style="background:var(--daily)"></span> Daily Notes
          <span class="filter-count">{counts.get('daily',0)}</span></label>
        <label class="filter-item"><input type="checkbox" data-type="instruction" checked>
          <span class="dot" style="background:var(--instr)"></span> Instructions
          <span class="filter-count">{counts.get('instruction',0)}</span></label>
        <label class="filter-item"><input type="checkbox" data-type="session" checked>
          <span class="dot" style="background:var(--session)"></span> Sessions
          <span class="filter-count">{counts.get('session',0)}</span></label>
      </div>
      <div id="detail-panel">
        <div id="detail-badge" class="detail-badge"></div>
        <div id="detail-title">Click any node to inspect</div>
        <div id="detail-file"  class="detail-meta"></div>
        <div id="detail-date"  class="detail-meta"></div>
        <div id="detail-text"></div>
      </div>
      <div class="gen-ts">Generated {generated_at}</div>
    </div>
  </div>
  <div id="main">
    <div id="tab-bar">
      <button class="tab active" data-tab="projector">3D Projector</button>
      <button class="tab"        data-tab="graph">Knowledge Graph</button>
      <button class="tab"        data-tab="timeline">Timeline</button>
    </div>
    <div id="tab-content">
      <div class="tab-panel active" id="panel-projector"><div id="plot-projector"></div></div>
      <div class="tab-panel"        id="panel-graph">    <div id="plot-graph"></div></div>
      <div class="tab-panel"        id="panel-timeline"> <div id="plot-timeline"></div></div>
    </div>
  </div>
</div>
<script>{js}</script>
</body>
</html>"""

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Building Ana's Memory Dashboard...")

    print("  -> Loading embeddings from QMD...")
    records, embeddings = load_data()

    print(f"  -> Running UMAP 3D on {len(records)} chunks...")
    coords3d = project(embeddings, 3)

    print("  -> Running UMAP 2D...")
    coords2d = project(embeddings, 2)

    print("  -> Computing semantic edges...")
    edges = compute_edges(embeddings)
    print(f"  -> {len(edges)} edges (similarity >= {EDGE_THRESHOLD})")

    print("  -> Building figures...")
    f3d = fig_projector_3d(coords3d, records)
    fg  = fig_knowledge_graph(coords2d, records, edges)
    ftl = fig_timeline(records)

    print("  -> Generating HTML...")
    html = build_html(f3d, fg, ftl, records, edges)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")

    size_kb = OUTPUT.stat().st_size // 1024
    print(f"\n  Done! {size_kb} KB written to {OUTPUT}")
    print(f"  Serve: python3 -m http.server 9090 --directory {OUTPUT.parent}")
    print(f"  Open:  http://localhost:9090/dashboard.html")


if __name__ == "__main__":
    main()
