#!/bin/bash
# Ana's Brain — build and serve
# Run from inside the container:
#   bash run-dashboard.sh          # build + serve on :9090
#   bash run-dashboard.sh --build  # build only
#   bash run-dashboard.sh --serve  # serve only (skip rebuild)
#
# Then open: http://<hostname>:9090/brain.html

set -e
export PATH="$HOME/.local/bin:$PATH"
DASHBOARD_DIR="/home/node/.openclaw/workspace/tools/memory-dashboard"
PORT="${DASHBOARD_PORT:-9090}"

BUILD=true
SERVE=true
if [[ "$1" == "--build" ]]; then SERVE=false; fi
if [[ "$1" == "--serve" ]]; then BUILD=false; fi

cd "$DASHBOARD_DIR"

if $BUILD; then
    echo "[$(date)] Building brain data..."
    python3 build_graph.py
    echo "[$(date)] Build complete."
fi

if $SERVE; then
    echo ""
    echo "  Serving on http://localhost:${PORT}/brain.html"
    echo "  Press Ctrl+C to stop."
    echo ""
    exec python3 -m http.server "$PORT" --directory "$DASHBOARD_DIR" --bind 0.0.0.0
fi
