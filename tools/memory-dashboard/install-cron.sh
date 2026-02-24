#!/bin/bash
# Install cron job for memory dashboard updates (every 6 hours)
# Run as root or with sudo

set -e

CRON_ENTRY="0 */6 * * * * export PATH=\"\$HOME/.local/bin:\$PATH\" && /usr/bin/python3 /home/node/.openclaw/workspace/tools/memory-dashboard/build_dashboard.py >> /tmp/dashboard-cron.log 2>&1"

echo "Installing cron job for memory dashboard..."
echo "$CRON_ENTRY" | crontab -

echo "✓ Cron job installed!"
echo ""
echo "Verify installation:"
crontab -l
echo ""
echo "Log file: /tmp/dashboard-cron.log"
