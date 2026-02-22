#!/bin/bash
# Daily appreciation message for Mr. Grey
# Runs daily at 10:28 AM IST

cd /home/node/.openclaw/workspace

# Generate and send voice message to Mr. Grey
MESSAGE="Just wanted to say how much you're appreciated, Mr. Grey. Your support and kindness mean more than you know. Thank you for being you."

openclaw tools tts --text "$MESSAGE" --channel telegram | \
openclaw tools message --action send --channel telegram --target 8387298410 --asVoice true

echo "Daily appreciation sent at $(date)"
