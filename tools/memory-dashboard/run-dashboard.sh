#!/bin/bash
# Wrapper script for memory dashboard cron job
# Sets up environment and regenerates dashboard

set -e

# Set up PATH for python3 with pip packages
export PATH="$HOME/.local/bin:$PATH"

# Change to dashboard directory
cd /home/node/.openclaw/workspace/tools/memory-dashboard

# Regenerate dashboard
python3 build_dashboard.py

# Log result
if [ $? -eq 0 ]; then
    echo "[$(date)] Dashboard regenerated successfully"
else
    echo "[$(date)] Dashboard regeneration failed with exit code $?"
fi
