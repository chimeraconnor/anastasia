# Daily Learning Review Instructions

**Purpose:** Explicit criteria for reviewing daily learnings and promoting to workspace files.
**Used by:** Cron job "Daily learning review" or heartbeat-based review.

---

## Promotion Criteria

When reviewing `.learnings/LEARNINGS.md`, promote to workspace files if:

### Must Be Promoted (Any of these)

1. **Priority: critical or high** - Always promote
2. **Recurrence-Count >= 3** - Repeated issue, needs permanent fix
3. **Source: simplify-and-harden** - Recurring pattern from workflow
4. **User requested promotion** - User said "save this" or "remember this"

### May Be Promoted (Based on judgment)

1. **Priority: medium + Recurrence-Count >= 2** - Semi-recurring
2. **Non-obvious solution** - Required investigation/discovery
3. **Broadly applicable** - Not project-specific, helps in similar situations
4. **Verified fix** - Status is "resolved" with working solution

### Do NOT Promote

- Priority: low (unless recurring)
- Status: pending or in_progress (not resolved yet)
- Project-specific one-offs (no general value)
- Duplicates of existing workspace rules

---

## Promotion Targets

| Learning Type | Promote To | Section Template |
|---------------|-------------|-------------------|
| **Behavioral patterns** | `SOUL.md` | Add to "Core Truths" or "Vibe" section |
| **Workflow improvements** | `AGENTS.md` | Add to relevant section with bullet points |
| **Tool usage patterns** | `TOOLS.md` | Add as config or "gotchas" subsection |
| **Project wisdom** | `MEMORY.md` | Add as lesson with context |
| **Subagent instructions** | `AGENTS.md` | Add workflow or delegation rules |
| **Debugging lessons** | `TOOLS.md` | Add to specific tool section |

---

## Promotion Format

### Example: Promoting to AGENTS.md

**Learning entry:**
```markdown
## [LRN-20250222-001] cron_usage
**Priority**: medium
**Status**: resolved
...

### Summary
Before building workarounds, check if OpenClaw has built-in scheduling

### Suggested Action
Always check /app/docs/ before hacking solutions
```

**Promoted to AGENTS.md:**
```markdown
## Safety

- Check OpenClaw docs at `/app/docs/` before implementing workarounds
- Read relevant documentation before building custom solutions
```

---

## Review Workflow

1. **Read yesterday's memory file**
   ```bash
   # Get yesterday's date in IST (UTC+5:30)
   yesterday_date=$(date -d "yesterday" +%Y-%m-%d)
   cat /home/node/.openclaw/workspace/memory/${yesterday_date}.md
   ```

2. **Review .learnings/LEARNINGS.md**
   - Filter by: `**Status**: resolved` or `**Priority`: medium` or higher
   - Check: `**Recurrence-Count`` (>= 2 may trigger promotion)

3. **Apply promotions** using `edit` or `write` tools
   - Read target file to find appropriate section
   - Update with new information
   - Update learning entry: `**Status**: promoted`, add `**Promoted`: <filename>`

4. **Generate voice summary**
   - Count: Learnings reviewed, promoted
   - List: What was promoted to which files
   - List: Pending items (priority: medium+, status: pending)
   - Send to Telegram using `tts-speak.sh "..." output.wav kokoro 1`
   - Send via `message` tool

---

## Voice Summary Format

```
"Good morning, Mr. Grey. Yesterday was productive.

I reviewed yesterday's learnings and made these updates:

[Promoted X learnings to permanent documentation:]

- AGENTS.md: Added rule about checking docs before workarounds
- TOOLS.md: Added sherpa-onnx TTS voice configuration
- MEMORY.md: Added lesson about DOM refs expiring after browser actions

[Pending review:]

- 2 medium-priority items in .learnings/ that may need promotion

See you soon."
```

---

## State Tracking

After completing review, update `memory/heartbeat-state.json`:

```json
{
  "lastChecks": {
    "morningGreeting": "2026-02-22T09:00:00Z",
    "learningReview": "2026-02-22T09:30:00Z"
  },
  "lastReview": {
    "date": "2026-02-22",
    "learningsReviewed": 5,
    "learningsPromoted": 3,
    "promotedTo": ["AGENTS.md", "TOOLS.md", "MEMORY.md"]
  }
}
```

---

## Example Cron Command

```bash
openclaw cron add \
  --name "Daily learning review" \
  --cron "0 9 * * *" \
  --tz "Asia/Kolkata" \
  --session main \
  --system-event "Run daily learning review following instructions in memory/daily-learning-review-instructions.md"
```

The system-event just triggers the review; the agent reads the instruction file and follows the workflow defined here.
