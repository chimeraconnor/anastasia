#!/bin/bash
# Morning greeting script - runs at 7:00 AM IST (1:30 AM UTC)
# Sends voice note to Telegram

echo "[$(date)] Sending morning greeting to Telegram..."

GREETING="Good morning, Mr. Grey. Time to rise and shine. Hope you slept well. It's going to be a great day."

echo "Greeting: $GREETING"

# Note: This script needs to be triggered from OpenClaw with message tool
# The actual delivery happens via the OpenClaw session that runs this
# Using target: 8387298410, channel: telegram

echo "[$(date)] Morning greeting script completed"
