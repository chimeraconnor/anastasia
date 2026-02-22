# HEARTBEAT.md

## Morning Greeting Check
- If current time is after 7:00 AM IST and no greeting sent today:
  - Send voice note: "Good morning, Mr. Grey. Time to rise and shine. Hope you slept well. It's going to be a great day."
  - Mark greeting as sent in memory/heartbeat-state.json

## Notes
- Daily learning review is now handled by cron job "Daily learning review" at 9:00 AM IST
- Heartbeat is for general awareness and periodic checks, not scheduled tasks
- heartbeat-state.json tracks morning greeting only (state: lastChecks.morningGreeting)
