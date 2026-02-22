# TOOLS.md - Local Notes

## OpenClaw Infrastructure

### Finding OpenClaw Binaries
- `openclaw` CLI is NOT in system PATH
- Binaries live in package directories: `/app/packages/*/node_modules/.bin/openclaw`
- Common path: `/app/packages/clawdbot/node_modules/.bin/openclaw`
- To find all: `find / -name "openclaw" -type f -executable 2>/dev/null`

### OpenClaw Cron System
- **Use OpenClaw's built-in cron first** — don't default to system crontab
- Command: `openclaw cron add` (via full path)
- Supports: `--cron "expr" --tz "IANA"` for timezone-aware scheduling
- Common issue: main session jobs require `--system-event`, isolated jobs use `--message`
- Docs location: `/app/docs/cli/cron.md`

## ZAI API Quota & Models

### Current Plan Status
- **Plan:** Grandfathered Lite (bought before Feb 12, 2026 cutoff)
- **Renewal:** Quarterly auto-renewal enabled
- **No weekly limits** — 5-hour dynamic quota only (~80 prompts, resets every 5 hours)

### Token Limits
- **Weekly cap:** ~40M tokens (resets **Saturday 12:51 PM IST**)
- **Account level:** Lite

### Model Selection Guidelines (2026-02-21)
- **Use GLM-4.7-FlashX for:** Simple data fetching, parsing, formatting, quick lookups, summarization
- **Use GLM-4.7 for:** Complex multi-step workflows, planning, nuanced decisions, coding/debugging tricky issues
- **Both share same token bucket** — match model to task complexity

## SearXNG Web Search

### Self-Hosted Instance
- **URL:** http://89.167.66.83:8888
- **Skill:** `searxng-self-hosted` installed from ClawHub

### Basic Usage
```bash
# Basic search
curl "$SEARXNG_URL/search?q=your+query&format=json"

# With categories (general, images, news, videos, it, science)
curl "$SEARXNG_URL/search?q=query&categories=images&format=json"

# With language
curl "$SEARXNG_URL/search?q=query&language=en-US&format=json"
```

## Telegram

- **Mr. Grey's ID:** 8387298410

## Docker/VPS Setup Note (2026-02-22)

**Volume Mapping:**
- **Host path:** `/root/.openclaw/workspace/` (files persist here)
- **Container path:** `/home/node/.openclaw/workspace/` (mapped via volume)
- **Environment variable:** `OPENCLAW_WORKSPACE_DIR=/root/.openclaw/workspace/` (host path, for reference)

**What this means:**
- Everything I save to `/home/node/.openclaw/workspace/` persists to `/root/.openclaw/workspace/` on your host
- The environment variable shows the **host path** (for reference), not the container path
- Use `/home/node/.openclaw/workspace/` for all file operations inside container

**Persistent storage:**
- All files saved to `/home/node/.openclaw/workspace/` survive container restarts
- Volume mount ensures they persist to your host drive at `/root/.openclaw/workspace/`

## Sherpa-ONNX TTS

### Models Installed

| Model | Path | Speakers | Languages | Active |
|-------|------|-----------|----------|--------|
| **Kokoro v1.0** ⭐ | `/home/node/kokoro-tts-standalone/models/kokoro-multi-lang-v1_0/` | 55 (0-54) | EN + ZH | Yes |
| Piper VITS | `~/.openclaw/tools/sherpa-onnx-tts/tts-models/vits-piper-en_US-gladys/` | 1 | EN | No |
| LibriTTS | `~/.openclaw/tools/sherpa-onnx-tts/tts-models/vits-piper-en_US-libritts_r-medium/` | 904 | EN | No |

### Wrapper Script

**Location:** `~/.openclaw/tools/tts-speak.sh`

**Usage:**
```bash
tts-speak.sh "Text to speak" [output_file] [model_type] [speaker_id]

# Examples:
tts-speak.sh "Hello" output.wav kokoro 1     # af_bella (Anastasia)
tts-speak.sh "Hello" output.wav kokoro 6     # af_nicole (default)
```

### Voice IDs (Kokoro v1.0)

| sid | Voice | Accent | Style |
|-----|-------|--------|-------|
| 0 | af | American | Standard female |
| 1 | af_bella ⭐ | American | Softer, younger - **Anastasia's voice** |
| 6 | af_nicole | American | Clear, articulate - **Default voice** |
| 10 | am_adam | American Male | |
| 20 | bf_emma | British Female | Elegant, refined |
| 30 | bm_george | British Male | |

### Anastasia's Voice Configuration

**Selected Voice:** af_bella (ID 1)
**Why:** Soft, sweet tone with subtle vulnerability — fits Anastasia's character

**For Subagents:** Always specify speaker ID 1 explicitly:
```bash
# Tell subagents to use:
tts-speak.sh "Text" output.wav kokoro 1
```

**Or edit wrapper default:**
```bash
# Edit ~/.openclaw/tools/tts-speak.sh
SID="${SPEAKER_ID:-1}"  # Changed from 6
```

### Notes
- Kokoro v1.1 was downloaded but not configured (wrapper uses v1.0)
- sherpa-onnx-tts skill wrapper has ESM issues → using direct binary calls
- Out-of-vocabulary words are skipped with warning

## Anastasia's GitHub Account (2026-02-22)

**Account:** chimeraconnor
**Password:** anacoder1212
**Email:** mediaduck42@gmail.com

**Purpose:**
- Backup all code I write
- Collaboration with Mr. Grey

**Rule:**
- Whenever I write or modify code → add/commit/push to repos
- Mr. Grey can pull changes to review or collaborate

**Git Config:**
- SSH keys configured for authentication
- Git will automatically use SSH for all GitHub operations
- Workspace: `/home/node/.openclaw/workspace/`

## Anastasia's Backup Repository (2026-02-22)

**Repository:** https://github.com/chimeraconnor/anastasia-backup
**Purpose:** Complete backup of Anastasia Steele for restoration if deleted

**What's backed up:**
- Core identity files (SOUL.md, IDENTITY.md, USER.md, AGENTS.md, HEARTBEAT.md, MEMORY.md, TOOLS.md, PROJECTS.md)
- Memory files (memory/YYYY-MM-DD.md)
- Skills (searxng-self-hosted, self-improving-agent)
- Tools (sherpa-onnx-tts, tts-speak.sh, runtime binaries)
- Scripts (daily-appreciation, morning-greeting, CRON_SETUP.md)

**What's NOT backed up (too large for GitHub):**
- Large TTS model files (>100MB):
  - `backup/tools/sherpa-onnx-tts/kokoro-multi-lang-v1_1/model.onnx` (310MB)
  - `backup/tools/sherpa-onnx-tts/kokoro-multi-lang-v1_1/voices.bin` (51MB)
- Model archives (>50MB, GitHub warns):
  - `backup/tools/tts-models/piper-gladys.tar.bz2` (64MB)
  - `backup/tools/tts-models/piper-libritts-medium.tar.bz2` (78MB)
  - `backup/tools/tts-models/vits-piper-en_US-glados/en_US-glados.onnx` (60MB)
  - `backup/tools/tts-models/vits-piper-en_US-libritts_r-medium/en_US-libritts_r-medium.onnx` (74MB)

**To restore Anastasia:**
1. Clone: `git clone https://github.com/chimeraconnor/anastasia-backup.git`
2. Copy files to workspace: `cp -r backup/* /path/to/workspace/`
3. Re-download large TTS models if needed (they're excluded from backup)

**Note:** TTS models can be re-downloaded from original sources if needed. They're not critical for restoration since they can be reinstalled.
