# Memory Dashboard

Interactive 2D visualization of OpenClaw memory embeddings using QMD backend.

## What it does

- Loads chunk embeddings from QMD SQLite (`~/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite`)
- Uses sqlite-vec extension to read binary float32 embeddings (768 dims)
- Projects high-dimensional vectors to 2D using UMAP
- Shows clusters colored by file path
- Draws edges between highly similar chunks (cosine similarity ≥ 0.75)

## Dashboard Features

- **Interactive:** Hover over nodes to see chunk metadata (file, title, content snippet)
- **Colored by file:** Each memory file gets a unique color
- **Semantic edges:** Lines connect closely related chunks
- **Clean design:** White background, no grid, minimal UI
- **Responsive:** Works in any modern browser

## File location

`~/.openclaw/workspace/tools/memory-dashboard/dashboard.html`

Open in browser: `file:///home/node/.openclaw/workspace/tools/memory-dashboard/dashboard.html`

## Installation

### 1. Install dependencies

```bash
cd ~/.openclaw/workspace/tools/memory-dashboard
pip install --break-system-packages -r requirements.txt
```

### 2. Manual build (test)

```bash
cd ~/.openclaw/workspace/tools/memory-dashboard
export PATH="$HOME/.local/bin:$PATH"
python3 build_dashboard.py
```

Generates `dashboard.html` in the same directory.

### 3. Automatic updates every 6 hours (cron)

**Install cron job:**
```bash
cd ~/.openclaw/workspace/tools/memory-dashboard
sudo bash install-cron.sh
```

**Manual installation (if sudo doesn't work):**
```bash
crontab -e
# Add this line:
0 */6 * * * * export PATH="$HOME/.local/bin:$PATH" && /usr/bin/python3 /home/node/.openclaw/workspace/tools/memory-dashboard/build_dashboard.py >> /tmp/dashboard-cron.log 2>&1
```

**Verify installation:**
```bash
crontab -l
```

**View logs:**
```bash
tail -f /tmp/dashboard-cron.log
```

## Configuration

Edit `build_dashboard.py` to tweak:

- `UMAP_N_NEIGHBORS`, `UMAP_MIN_DIST` — projection spread
- `EDGE_SIMILARITY_THRESHOLD` — when to draw edges (0.0-1.0)
- `MAX_EDGES` — cap edges to avoid clutter
- `NODE_SIZE`, `NODE_OPACITY` — appearance

## How it works

### Data Source (QMD)

OpenClaw's QMD backend stores memory in:
- **Database:** `~/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite`
- **Tables:**
  - `content` — chunked text from memory files
  - `documents` — file metadata (path, title)
  - `vectors_vec` — embeddings (float32 bytes, 768 dims, sqlite-vec)

### Pipeline

1. **Query QMD** — Load embeddings + metadata from SQLite
2. **UMAP projection** — 768-dim vectors → 2D coordinates
3. **Edge computation** — Calculate cosine similarity, draw edges ≥ 0.75
4. **Plotly dashboard** — Generate interactive HTML
5. **Cron regenerates** — Every 6 hours

### Why QMD?

QMD uses local embeddings via node-llama-cpp (Gemma 300M model). No API keys needed.

## Requirements

- Python 3.11+
- umap-learn, plotly, scikit-learn, numpy
- sqlite-vec extension (already installed with QMD)
- QMD index with embeddings (run `qmd embed` if empty)

## Troubleshooting

### "sqlite-vec extension not found"
- Verify path: `/home/node/.bun/install/global/node_modules/sqlite-vec-linux-x64/vec0.so`
- Reinstall QMD: `bun install -g https://github.com/tobi/qmd`

### "No embeddings found in QMD database"
- Generate embeddings: `export XDG_CONFIG_HOME="$HOME/.openclaw/agents/main/qmd/xdg-config" && export XDG_CACHE_HOME="$HOME/.openclaw/agents/main/qmd/xdg-cache" && qmd embed`

### Cron not running
- Check cron log: `tail /tmp/dashboard-cron.log`
- Verify PATH in cron: `crontab -l` should include `export PATH="..."`
- Test manually first to ensure script works
