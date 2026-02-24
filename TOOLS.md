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

## Research Workflow (2026-02-24)
**Rule from Mr. Grey:** When asked about something new:
1. Use my own general knowledge first
2. Then research using SearXNG to verify/enhance
3. SearXNG is free to use — no quota concerns

**Implementation:** Use the `web_search` tool with the SearXNG option, or call the searxng skill directly.

## Telegram

- **Mr. Grey's ID:** 8387298410

## Discord

- **User ID:** 1262353633089949718
- **Server ID:** 1475190771727597792
- **Token:** Configured in OpenClaw config
- **Status:** Enabled

### Discord Voice Messages (Custom Skill) — **USE THIS, NOT native `asVoice`**

**⚠️ PRECEDENCE:** Always use this skill instead of the native `message(asVoice=true)` parameter. The native implementation is broken (Issue #16103).

**Location:** `~/.openclaw/workspace/skills/discord-voice/`

Sends audio files as native Discord voice messages with waveform visualization. Implements the full Discord voice message protocol directly.

**Usage (Preferred Method):**
```bash
python3 ~/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py \
  --channel-id 1475190772830568682 \
  --audio-file /path/to/audio.wav \
  --verbose
```

**Integration with TTS:**
```bash
# Generate voice with TTS, then send as Discord voice message
~/.openclaw/tools/tts-speak.sh "Your message here" /tmp/audio.wav kokoro 1
python3 ~/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py \
  --channel-id 1475566112019058758 \
  --audio-file /tmp/audio.wav
```

**Requirements:**
- `python3`, `ffmpeg`, `ffprobe` (all installed on host)
- Discord bot token (auto-read from OpenClaw config)

**Features:**
- ✅ Auto-converts any audio format to OGG/Opus
- ✅ Generates 256-sample waveform from audio amplitude
- ✅ Detailed error messages per step (conversion, upload, send)
- ✅ 3-step Discord API flow (upload URL → CDN upload → voice message send)
- ✅ Returns JSON with message_id on success

**Why not native `asVoice`?**
- Native `message(action="send", asVoice=true, ...)` returns generic "Error" even when it works
- This skill gives proper error messages and reliable success confirmation
- Implements Discord's voice message protocol directly via Python

**Protocol Details:**
1. `POST /channels/{id}/attachments` — get pre-signed upload URL
2. `PUT {upload_url}` — upload OGG/Opus to Discord's CDN  
3. `POST /channels/{id}/messages` — send with `flags: 8192` (IS_VOICE_MESSAGE), duration, and base64 waveform

### Voice-Call Plugin (Phone Calls)

**Purpose:** Actual phone calls (Twilio, Telnyx, Plivo) - NOT text-to-speech (TTS)

**Configuration:**
- Configured via gateway config: `plugins.entries.voice-call.enabled` and `plugins.entries.voice-call.config`
- Location: `/root/.openclaw/config.json` or via `openclaw config set`
- Not a CLI command - it's a plugin entry point

**Usage:**
- User in web UI sends "call me" → OpenClaw starts voice call to phone
- Uses Twilio/Telnyx/Plivo for actual phone calls
- **Critical distinction:** "Voice call" = phone calls, "Voice note" = TTS audio (sherpa-onnx)

**Testing:**
- Use `provider: "mock"` for dev/testing (no network, no costs)
- Check if loaded: `openclaw gateway call plugins.list --params '{}'`

**Key lesson:** Don't confuse "voice call" (phone) with "voice note" (audio file). They're completely different systems.

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

**Critical distinction:**
- **Host path** (`/root/.openclaw/workspace/`) is OUTSIDE the container
- **Container path** (`/home/node/.openclaw/workspace/`) is INSIDE the container
- Environment variable `OPENCLAW_WORKSPACE_DIR` shows the host path for reference, but use container path for operations

## Sherpa-ONNX TTS

### Models Installed

| Model | Path | Speakers | Languages | Active |
|-------|------|-----------|----------|--------|
| **Kokoro v1.0** ⭐ | `/home/node/.openclaw/workspace/.kokoro-v1.0/` | 55 (0-54) | EN + ZH | Yes |
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
- **Preferred:** use the `sherpa_tts` tool directly — it routes through `tts-speak.sh` automatically
- **Fallback (shell/subagent):** call `tts-speak.sh` directly — never call `sherpa-onnx-offline-tts` binary directly
- Direct binary calls skip all preprocessing → unnatural pauses, spoken punctuation, broken contractions
- Preprocessing lives in `~/.openclaw/tools/tts-preprocess.py` (pure Python stdlib, no deps)
- Kokoro v1.1 was downloaded but not configured (wrapper uses v1.0)
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

**Main Repository:** https://github.com/chimeraconnor/anastasia
- Contains all code, identity files, memories, tools, skills, scripts
- Complete backup — can restore Anastasia by cloning this repo
- 1,559 files backed up (excludes large TTS model files)

**GitHub CLI (`gh`) Authentication (2026-02-24)**
- **Status:** Logged in via PAT token
- **Token stored:** `~/.config/gh/hosts.yml`
- **Current token expires:** March 26, 2026 — regenerate before then
- **Authentication method:** `echo "TOKEN" | gh auth login --with-token`
- **Device code flow is broken** — don't use `gh auth login --web`, it times out
- **What it enables:**
  - GitHub API queries (repos, users, organizations)
  - Create/manage issues and pull requests
  - Search repositories and code
  - View PR reviews, CI runs, workflows
  - Access to any public repo, private repos you have explicit access to

**Rule:** Always use `--with-token` method. Don't waste time on device code links — they don't work reliably in this environment.
