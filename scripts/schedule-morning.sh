#!/bin/bash
# Calculate seconds until 7:00 AM IST (1:30 AM UTC)
# This script should be run before the target time

TARGET_TIME="01:30"
current_date=$(date +%Y-%m-%d)
target_epoch=$(date -d "$current_date $TARGET_TIME:00 UTC" +%s)
current_epoch=$(date +%s)

if [ $target_epoch -le $current_epoch ]; then
    # If today's time has passed, schedule for tomorrow
    target_epoch=$(date -d "$current_date $TARGET_TIME:00 UTC tomorrow" +%s)
fi

seconds_until=$((target_epoch - current_epoch))
hours_until=$((seconds_until / 3600))
minutes_until=$(((seconds_until % 3600) / 60))

echo "Scheduling morning greeting for $TARGET_TIME UTC (7:00 AM IST)"
echo "Starting in: $hours_until hours, $minutes_until minutes"

# Sleep until the target time, then run the greeting
sleep $seconds_until && /home/node/.openclaw/workspace/scripts/morning-greeting.sh &
echo "Scheduled! PID: $!"
