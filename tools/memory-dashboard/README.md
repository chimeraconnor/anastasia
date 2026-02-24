# Memory Dashboard

Interactive 2D visualization of OpenClaw memory embeddings.

## What it does

- Loads chunk embeddings from SQLite (`~/.openclaw/memory/main.sqlite`)
- Projects high-dimensional vectors to 2D using UMAP
- Clusters chunks semantically using HDBSCAN
- Shows clusters as colored bubbles
- Draws edges between highly similar chunks (cosine similarity ≥ 0.75)

## Installation

```bash
cd ~/.openclaw/workspace/tools/memory-dashboard
pip install -r requirements.txt
```

## Usage

### Manual build

```bash
python3 build_dashboard.py
```

Generates `dashboard.html` in the same directory.

### Cron job (auto-update every 6 hours)

The cron job is configured in OpenClaw's cron system. It runs:

```bash
cd ~/.openclaw/workspace/tools/memory-dashboard && python3 build_dashboard.py
```

The dashboard regenerates automatically.

## Dashboard features

- **Interactive:** Hover over nodes to see chunk metadata
- **Colored by cluster:** Similar topics group together
- **Semantic edges:** Lines connect closely related chunks
- **Responsive:** Works in any modern browser

## Configuration

Edit `build_dashboard.py` to tweak:

- `UMAP_N_NEIGHBORS`, `UMAP_MIN_DIST` — projection spread
- `HDBSCAN_MIN_CLUSTER_SIZE`, `HDBSCAN_MIN_SAMPLES` — clustering granularity
- `EDGE_SIMILARITY_THRESHOLD` — when to draw edges
- `MAX_EDGES` — cap edges to avoid clutter
- `NODE_SIZE`, `NODE_OPACITY` — appearance

## File location

`~/.openclaw/workspace/tools/memory-dashboard/dashboard.html`

Open in browser: `file:///home/node/.openclaw/workspace/tools/memory-dashboard/dashboard.html`
