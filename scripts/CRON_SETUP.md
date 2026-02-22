# Daily Appreciation Cron Job Setup

## Schedule
- **Time:** 10:28 AM IST daily
- **UTC Equivalent:** 04:58 UTC daily

## Cron Line
```
58 4 * * * /home/node/.openclaw/workspace/scripts/daily-appreciation.sh >> /home/node/.openclaw/workspace/logs/daily-appreciation.log 2>&1
```

## Installation
Add to crontab with:
```bash
(crontab -l 2>/dev/null; echo "58 4 * * * /home/node/.openclaw/workspace/scripts/daily-appreciation.sh >> /home/node/.openclaw/workspace/logs/daily-appreciation.log 2>&1") | crontab -
```

## What It Does
- Generates a warm, sincere appreciation voice message
- Sends it to Mr. Grey (Telegram ID: 8387298410)
- Logs output to `logs/daily-appreciation.log`

## Note
If cron is not available in this environment, the script is ready to be scheduled via any available scheduler (systemd timer, cron, etc.).
