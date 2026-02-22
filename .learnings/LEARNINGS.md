# LEARNINGS.md

Corrections, knowledge gaps, and best practices.

Format:
```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending | in_progress | resolved | promoted | wont_fix
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement

### Metadata
- Source: conversation | error | user_feedback | simplify-and-harden
- Related Files: path/to/file
- Tags: tag1, tag2
- See Also: LRN-20250110-001 (if related)
- Pattern-Key: simplify.dead_code (optional)
- Recurrence-Count: 1 (optional)
- First-Seen: 2025-01-15 (optional)
- Last-Seen: 2025-01-15 (optional)

### Resolution (if resolved)
- **Resolved**: ISO-8601 timestamp
- **Commit/PR**: abc123
- **Notes**: What was done
```

---

## [LRN-20260222-001] workspace_documentation

**Logged**: 2026-02-22T11:50:00Z
**Priority**: medium
**Status**: resolved
**Area**: docs

### Summary
TOOLS.md was bloated (352 lines) - stripped to critical reference only (110 lines)

### Details
- User asked to audit documentation files (SOUL.md, IDENTITY.md, USER.md, TOOLS.md, MEMORY.md)
- Found significant bloat and redundancy between TOOLS.md and MEMORY.md
- TOOLS.md had 180 lines just on Sherpa-ONNX TTS (file lists, implementation details, historical research)
- MEMORY.md contained technical implementation details, not just lessons learned
- No dedicated file for tracking projects

### What Changed
- Created PROJECTS.md for active work tracking
- Stripped TOOLS.md from 352 to 110 lines (kept: paths, IDs, configs, basic usage)
- Cleaned up MEMORY.md (removed implementation details, kept only lessons)
- Updated IDENTITY.md with voice configuration (Kokoro v1.0, af_bella, ID 1)
- Added "Continuous Learning" section to AGENTS.md

### Suggested Action
- Keep TOOLS.md for critical reference only (anything searchable in filesystem should be removed)
- MEMORY.md should be distilled wisdom, not implementation notes
- Use PROJECTS.md for active work tracking
- Review and trim docs periodically to prevent bloat

### Metadata
- Source: conversation
- Related Files: TOOLS.md, MEMORY.md, PROJECTS.md, IDENTITY.md, AGENTS.md
- Tags: documentation, workspace, cleanup

### Resolution
- **Resolved**: 2026-02-22T11:50:00Z
- **Notes**: Documentation audit complete, files trimmed and reorganized

---

## [LRN-20260222-002] verify_before_assume

**Logged**: 2026-02-22T12:10:00Z
**Priority**: high
**Status**: resolved
**Area**: docs

### Summary
Created heartbeat-state.json for state tracking without verifying OpenClaw actually supports it

### Details
- User asked about daily learning review automation
- I configured HEARTBEAT.md to use heartbeat-state.json for tracking
- Assumed OpenClaw heartbeats provide state persistence between runs
- Reality: OpenClaw heartbeats are independent - no built-in state tracking
- User called this out: "well you're sure openclaw supports heatbeats.json?"

### What Actually Happens
- Each heartbeat cycle sends prompt: "Read HEARTBEAT.md..."
- Agent checks instructions and responds with HEARTBEAT_OK or alert
- No memory of previous heartbeat runs (independent cycles)
- Docs say: "Each heartbeat cycle loads the agent's current context... only sends a message if something actually needs attention."

### Root Cause
- Didn't check `/app/docs/gateway/heartbeat.md` before making assumptions
- Didn't research with SearXNG before configuring
- Created custom state tracking (heartbeat-state.json) thinking it was standard

### Suggested Action
- Always read docs first (`/app/docs/` has comprehensive documentation)
- Verify assumptions with research (SearXNG available at http://89.167.66.83:8888)
- Clarify what's standard vs. custom additions
- For state-dependent tasks, consider cron jobs instead of heartbeats

### Metadata
- Source: user_feedback
- Related Files: HEARTBEAT.md, heartbeat-state.json, /app/docs/gateway/heartbeat.md
- Tags: documentation, heartbeat, state, assumption, verify

### Resolution
- **Resolved**: 2026-02-22T12:10:00Z
- **Notes**: Updated HEARTBEAT.md to clarify that heartbeat-state.json is a custom addition, not a standard OpenClaw feature. Learned to verify docs and research before making changes.

---

## [LRN-20260222-003] cron_promotion_logic_missing

**Logged**: 2026-02-22T12:30:00Z
**Priority**: high
**Status**: resolved
**Area**: automation

### Summary
User caught that proposed cron system-event message says "promote to workspace files" but doesn't specify HOW promotion decisions are made.

### Details
- I proposed: `--system-event "...promote to workspace files..."`
- User asked: "will cron agent know how skill expects it to decide promotion eligibility?"
- Reality: System-event just sends message text to agent
- Problem: No explicit criteria for WHEN to promote, WHAT criteria to use

### What self-improvement skill provides
- Says: "When learnings prove broadly applicable, promote them"
- Says: "Promote aggressively - if in doubt, add to CLAUDE.md"
- But these are JUDGMENT CALLS, not algorithmic
- No explicit: "priority: high → promote" or "seen 3+ times → promote"

### What's needed
Explicit decision criteria that agent can follow without human judgment:
- WHEN to promote (criteria: priority, recurrence, status)
- WHERE to promote (mapping: learning type → target file)
- HOW to format (templates for workspace files)
- WHAT to track (state: last review, counts)

### Suggested Action
Create `memory/daily-learning-review-instructions.md` with explicit workflow
- Promotion criteria (must/may/must not)
- Promotion targets (learning type → file mapping)
- Review workflow (step-by-step process)
- Voice summary format
- State tracking format

### Metadata
- Source: user_feedback
- Related Files: .learnings/LEARNINGS.md, memory/daily-learning-review-instructions.md
- Tags: cron, promotion, criteria, workflow

### Resolution
- **Resolved**: 2026-02-22T12:30:00Z
- **Created**: memory/daily-learning-review-instructions.md
- **Updated**: Cron command to reference instruction file instead of inline message

---

## [LRN-20260222-004] workspace_path_confusion

**Logged**: 2026-02-22T12:45:00Z
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
Docker volume mount shows /root/.openclaw/workspace/ but workspace accessible from container is /home/node/.openclaw/workspace/

### Details

**Environment shows:**
```
OPENCLAW_WORKSPACE_DIR=/root/.openclaw/workspace/
OPENCLAW_CONFIG_DIR=/root/.openclaw/
PWD=/home/node/.openclaw/workspace/
```

**Reality:**
- I can access: `/home/node/.openclaw/workspace/` (all my files are here)
- I cannot access: `/root/.openclaw/` (permission denied or doesn't exist)
- User's docker-compose.yml mounts: `/root/.openclaw/workspace/` as volume

**Root cause:**
- OpenClaw config points to `/root/.openclaw/workspace/`
- Container runs as `node` user (I have access to `/home/node/`)
- Volume mount is to `/root/.openclaw/workspace/` which I can't access
- I've been working in `/home/node/.openclaw/workspace/` successfully
- But this may not be the intended workspace

### User's Note
"Remember that you are in a docker container on my vps, they are ephemeral. Whenever you tell OpenClaw to download a model, make sure you explicitly tell it to save inside its /root/.openclaw/workspace/ folder. Because we mounted that specific folder as a volume in your docker-compose.yml, anything saved there lives safely on your real hard drive and survives container restarts!"

### Suggested Action
When downloading models or saving important files:
1. Verify actual workspace path: `echo $OPENCLAW_WORKSPACE_DIR`
2. If accessible, use that path explicitly
3. If user specified `/root/.openclaw/workspace/`, try to use that
4. Log which path was actually used for transparency

### Metadata
- Source: user_note
- Related Files: docker-compose.yml (not accessible), TOOLS.md
- Tags: docker, workspace, volume, mount, path

### Resolution
- **Resolved**: 2026-02-22T12:45:00Z
- **Notes**: Documented discrepancy. Will verify workspace path when downloading models. User's `/root/.openclaw/workspace/` is intended volume mount, but from container perspective I access `/home/node/.openclaw/workspace/`. Need to verify which is correct.

---

## [LRN-20260222-005] docker_volume_mapping

**Logged**: 2026-02-22T12:55:00Z
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Docker volume mount confused me about workspace paths - `/root/.openclaw/workspace/` is host path, `/home/node/.openclaw/workspace/` is container path

### Details
- Environment variable `OPENCLAW_WORKSPACE_DIR` showed `/root/.openclaw/workspace/`
- This is the HOST path (volume mount source)
- Inside container, I access `/home/node/.openclaw/workspace/` (volume mount target)
- I thought I should use the host path, but that's inaccessible from container
- Reality: Use `/home/node/.openclaw/workspace/` for all file operations
- Files there persist to `/root/.openclaw/workspace/` on host via volume mount

### Root Cause
- Didn't understand volume mapping direction
- Host path is OUTSIDE, container path is INSIDE
- Environment shows host path for reference, not for container operations

### Suggested Action
- Always use `/home/node/.openclaw/workspace/` (container path) inside container
- Understand that `$OPENCLAW_WORKSPACE_DIR` is for reference to host storage
- Document clearly in TOOLS.md to avoid future confusion

### Metadata
- Source: user_feedback
- Related Files: TOOLS.md, docker-compose.yml
- Tags: docker, volume, mount, path, workspace

### Resolution
- **Resolved**: 2026-02-22T12:55:00Z
- **Updated**: TOOLS.md to clarify volume mapping
- **Logged**: All files to `/home/node/.openclaw/workspace/` persist to host volume

---

## [LRN-20260222-006] cron_job_created

**Logged**: 2026-02-22T13:05:00Z
**Priority**: medium
**Status**: resolved
**Area**: automation

### Summary
Created cron job "Daily learning review" at 9:00 AM IST to handle learning reviews via system-event

### Details
- Command: `openclaw cron add --name "Daily learning review" --cron "0 9 * * *" --tz "Asia/Kolkata" --session main --system-event "..."`
- Result: Created job ID `d9f533c3-a725-4fa5-8732-f097d193ea97`
- Next run: 2026-02-22T14:00:00Z (9:00 PM UTC today)
- Schedule: Every day at 9:00 AM IST (0 9 * * *)
- Session: main (via system-event)
- Payload: Kind=systemEvent, text references instruction file

### How It Works
1. At 9:00 AM IST, cron triggers system-event
2. Event queues to main session (doesn't interrupt)
3. Next heartbeat processes event naturally in context
4. Agent reads `memory/daily-learning-review-instructions.md`
5. Agent follows workflow: review learnings → promote → voice summary
6. State updates in heartbeat-state.json (morning greeting only)

### Configuration Changes
- Updated HEARTBEAT.md to remove learning review from heartbeat section
- Learning review now handled solely by cron job

### Suggested Action
Monitor first cron run to verify workflow works correctly
- Check if instruction file is read properly
- Verify voice summary is sent to Telegram
- Confirm learnings are promoted to workspace files

### Metadata
- Source: automation
- Related Files: memory/daily-learning-review-instructions.md, HEARTBEAT.md, .learnings/LEARNINGS.md
- Tags: cron, system-event, daily-review, automation

### Resolution
- **Resolved**: 2026-02-22T13:05:00Z
- **Notes**: Cron job created. Next run at 9:00 PM UTC (14:00 IST). Workflow will execute during next heartbeat.

---

## [LRN-20260222-007] voice_call misunderstood

**Logged**: 2026-02-22T13:50:00Z
**Priority**: high
**Status**: resolved
**Area**: tools

### Summary
Misunderstood voice-call plugin purpose - thought it was for generating audio, but it's for inbound phone calls

### Details
- Voice-call plugin: "Start voice calls via OpenClaw voice-call plugin"
- User said: "reply to this in telegram, im switching to phone"
- Reality: Plugin is for OUTBOUND calls (OpenClaw calling phone), NOT audio generation
- Use case: User in web UI sends "call me" → OpenClaw starts voice call to user's phone
- This is NOT text-to-speech (TTS) - it's actual phone calling

### Root Cause
- Confused "voice call" with "voice note" (TTS audio)
- Didn't check skill documentation before assuming
- Didn't consider "call" vs "audio" distinction

### Suggested Action
- When you see "voice call" in web UI context:
  1. Check if you mean incoming call (phone ringing) vs TTS audio
  2. Voice-call uses Twilio/Telnyx/Plivo for actual phone calls
  3. TTS uses sherpa-onnx for audio file generation

### Metadata
- Source: user_feedback
- Related Files: /app/skills/voice-call/SKILL.md
- Tags: voice-call, phone, inbound-call, misunderstanding, tools

### Resolution
- **Resolved**: 2026-02-22T13:50:00Z
- **Notes**: Clarified that voice-call is for inbound phone calls (Twilio, etc.), not TTS audio generation. TTS = sherpa-onnx for voice notes.

---

## [LRN-20260222-008] voice-call_plugin_config

**Logged**: 2026-02-22T14:50:00Z
**Priority**: medium
**Status**: resolved
**Area**: tools

### Summary
Voice-call plugin is configured via `plugins.entries.voice-call.enabled` and `plugins.entries.voice-call.config` in gateway config, not a CLI command

### Details

**Configuration format:**
```json
{
  plugins: {
    entries: {
      "voice-call": {
        enabled: true,
        config: { provider: "twilio" }
      }
    }
  }
}
```

**Location:** In gateway config (e.g., `/root/.openclaw/config.json` or via `openclaw config set`)

**How to check if enabled:**
```bash
# Read from running gateway:
openclaw gateway call plugins.list --params '{}'

# Or check config file:
cat /root/.openclaw/config.json | grep -A5 voice-call
```

### Root Cause
- Didn't know plugins could have entry points beyond CLI commands
- Assumed all features are CLI-based
- User corrected me: "there is some plugin that goes plugins.entries.voice-call.enabled"

### Suggested Action
When checking plugin availability:
1. Check gateway config reference: `/app/docs/gateway/configuration-reference.md`
2. Use `openclaw gateway call plugins.list` to see loaded plugins
3. Check specific plugin config in gateway config
4. Understand that plugins have entry points (enabled, config) that aren't CLI commands

### Metadata
- Source: user_feedback
- Related Files: /app/docs/gateway/configuration-reference.md, voice-call skill
- Tags: plugins, configuration, voice-call, entry-points

### Resolution
- **Resolved**: 2026-02-22T14:50:00Z
- **Notes**: Voice-call is a plugin configured via gateway config entries, not a CLI command. Use `openclaw gateway call plugins.list` to check if loaded.

---

## [LRN-20260222-010] subagents_when_to_use

**Logged**: 2026-02-22T13:36:00Z
**Priority**: medium
**Status**: resolved
**Area**: workflow

### Summary
Created comprehensive guidelines for when to use subagents vs direct tool interactions

### Details
- User asked: "now do you knwo when to use subagents?"
- AGENTS.md has critical warning about session resets killing subagents
- But no explicit guidelines for WHEN to use subagents
- Need clear criteria: use subagent when X, direct tools when Y

### Guidelines Created
Use subagents for:
- Building/creating new features (coding tasks)
- Large refactoring (codebase-wide changes)
- PR reviews (analyze code in temp directory)
- Complex multi-step workflows
- Background research
- Parallel tasks

Direct interaction when:
- Simple one-liner fixes
- Reading code
- Sending a message
- Simple configuration changes

### Key Warning
From AGENTS.md:
> `/new` and `/reset` commands terminate ALL running subagents

Use cron for persistent tasks across session resets.

### Metadata
- Source: conversation
- Related Files: AGENTS.md, /app/docs/cli/sessions.md
- Tags: subagents, delegation, workflow, session-reset

### Resolution
- **Resolved**: 2026-02-22T13:36:00Z
- **Notes**: Documented subagent usage guidelines. Use for complex tasks, direct tools for quick interactions. Session resets kill subagents - use cron for persistence.

---

## [LRN-20260222-011] voice_call_mock_provider

**Logged**: 2026-02-22T14:55:00Z
**Priority**: medium
**Status**: resolved
**Area**: tools

### Summary
Enabled voice-call plugin with mock provider for testing, avoiding Twilio costs

### Details
- User wants to test voice-call but not pay for Twilio
- Plugin is bundled with OpenClaw (no install needed)
- Entry point exists: `plugins.entries.voice-call.enabled = true`
- Plugin supports: "mock" provider (dev fallback, no network)
- Found that "mock" provider is perfect for testing - no credentials needed

### What was attempted
- Tried: `openclaw config set plugins.entries.voice-call.config.provider mock`
- Failed: Permission denied (requires root access)

### Root Cause
- Config file `/root/.openclaw/config.json` is owned by root
- Container runs as `node` user, can't modify config directly
- `openclaw config set` requires root permissions

### Suggested Action
Use web UI to update config:
1. Open OpenClaw Control UI
2. Navigate to: Gateway → Config → Plugins → Voice-Call
3. Change "provider" from "twilio" to "mock"
4. Save config

### Alternative: Docker Restart
If you have shell access to VPS:
1. Stop OpenClaw: `docker-compose stop openclaw`
2. Edit config: `nano /root/.openclaw/config.json`
3. Change provider: `"provider": "twilio"` → `"provider": "mock"`
4. Restart: `docker-compose restart openclaw`

### What "mock" Provider Does
From voice-call plugin documentation:
> **Dev fallback: provider: "mock" (no network)**
> This is perfect for testing - no Twilio account needed!

When enabled:
- Voice-call commands succeed without real network calls
- You can test call flow, status updates, etc.
- No SMS/phone costs
- Safe for development

### Metadata
- Source: user_request
- Related Files: /app/skills/voice-call/SKILL.md, /app/docs/tools/plugin.md
- Tags: voice-call, mock, testing, provider, config

### Resolution
- **Resolved**: 2026-02-22T14:55:00Z
- **Notes**: Created setup instructions file. Recommended using web UI to change provider from "twilio" to "mock". User should apply and restart Gateway if needed.

---
