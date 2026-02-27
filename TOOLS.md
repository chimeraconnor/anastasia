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
- **Discord channels:** Use glm-4.7, not k2p5 (kimi-coding)
  - k2p5 has rate limits → causes 5-10 minute delays
  - glm-4.7 has no rate limits → faster, more reliable
  - If Discord uses k2p5, switch to glm-4.7 in config

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
  --channel-id 1476287721277493269 \
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
- `python3`, `ffmpeg`, `ffprobe` (all installed in Docker container)
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

## TTS (Text-to-Speech) - Anastasia's Voice System

**Primary Skill:** `~/.openclaw/workspace/skills/anastasia-tts/`

**Default:** Pocket TTS with `azelma` voice (sounds like Anastasia)

### Quick Usage

```bash
# Default voice (Pocket/azelma)
~/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py "Hello, I'm Anastasia."

# Send to Discord automatically
~/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py "Hello" \
    --platform discord --channel-id 1476357999952920626

# Alternative voices
~/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py "Hello" \
    --engine kitten --voice Bella --speed 1.3
```

### Engine Options

| Engine | Default Voice | Speed Control | Best For |
|--------|--------------|---------------|----------|
| `pocket` | azelma | No | **Default** - Fast (2.1x RT) |
| `kitten` | Bella | Yes (0.8-1.5) | Higher quality, slower |
| `kokoro` | af_bella | Yes | Backup option |

### Female Voices (Anastasia-like)
- **pocket:** `azelma` (default), `fantine`, `cosette`, `eponine`
- **kitten:** `Bella`, `Luna`, `Rosie`, `Kiki`
- **kokoro:** `af_bella` (speaker 1)

### Legacy Tools (organized by engine)

**Location:** `/home/node/.openclaw/workspace/tools/tts/`

```
tts/
├── kokoro/     # Sherpa-ONNX Kokoro TTS
├── kitten/     # KittenTTS mini-0.8 scripts
└── pocket/     # PocketTTS scripts
```

**For direct engine access without the skill wrapper:**
```bash
# KittenTTS
/home/node/.openclaw/workspace/tts-py312/bin/python \
    ~/.openclaw/workspace/tools/tts/kitten/kitten-speak.py "Hello" output.wav Bella 1.3

# PocketTTS
python3 ~/.openclaw/workspace/tools/tts/pocket/pocket-speak.py "Hello" output.wav azelma
```

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

**Installed tools in Docker container:**
- `ffmpeg` 5.1.8 - audio/video conversion
- `ffprobe` 5.1.8 - media file inspection
- `python3` - for Discord voice skill and other Python scripts

**Disk Monitoring (2026-02-26)**
- **Monitor disk space regularly** — full disk causes crashes and prevents writes
- **Check usage with:** `df -h`
- **Clean large directories:**
  - `workspace/moshi-tts`, `workspace/CosyVoice` - TTS models (can be removed if not in use)
  - `/home/node/.cache` - uv cache (8GB), HuggingFace models (4.7GB)
  - `/home/node/.local/lib` - duplicate Python packages
- **Clean uv cache:** `uv cache clean` (frees ~8GB)
- **Rule:** When disk approaches 90%, clean up before it hits 100%

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

## Vercel Deployment Skill (2026-02-25)

**Location:** `~/.openclaw/workspace/skills/vercel-deploy/`

Complete workflow for deploying websites to Vercel with GitHub integration.

### Token Storage
- File: `.env.vercel` (workspace root)
- Format: `VERCEL_TOKEN=vcp_...`
- Load: `export $(cat .env.vercel | xargs)`

### Available Scripts
All in `skills/vercel-deploy/scripts/`:
- `create-vercel-project.sh <name> <owner/repo> [framework]` - Create Vercel project
- `deploy.sh <name> <owner/repo> [repo-id] [target]` - Deploy project
- `make-public.sh <project-id>` - Remove SSO protection

### Quick Usage
```bash
cd ~/.openclaw/workspace/skills/vercel-deploy

# Create project
./scripts/create-vercel-project.sh my-site chimeraconnor/my-site nextjs

# Deploy (need repo ID from GitHub API or previous project creation)
./scripts/deploy.sh my-site chimeraconnor/my-site 123456789 production

# Make public
PROJECT_ID=$(curl -s -H "Authorization: Bearer $VERCEL_TOKEN" https://api.vercel.com/v9/projects/my-site | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
./scripts/make-public.sh $PROJECT_ID
```

### API Endpoints
- `POST /v9/projects` - Create project
- `POST /v13/deployments` - Trigger deployment  
- `GET /v13/deployments/{id}` - Check status
- `PATCH /v9/projects/{id}` - Update settings (e.g., remove SSO)

### Frameworks Supported
Next.js, React, Vue, Nuxt, Svelte, Angular, Remix, Astro, and many more.

See full API docs: `skills/vercel-deploy/references/api.md`

## Memory Dashboard (2026-02-27)

**Location:** `tools/memory-dashboard/`

Interactive 3D visualization of Anastasia's knowledge base — memory, lessons, skills, and sessions clustered by semantic similarity.

### What It Does

The dashboard visualizes Anastasia's brain by:
- **Scanning workspace files** — MEMORY.md, skills/, sessions, identity files
- **Splitting into semantic sections** — Each `##`/`###` header becomes one brain node
- **Computing embeddings** — Hybrid approach using QMD's deep learning embeddings + TF-IDF fallback
- **3D projection** — UMAP reduces 768-dim vectors to 3D coordinates
- **Clustering** — OPTICS groups related concepts automatically
- **Auto-labeling** — Human-readable cluster names (e.g., "discord / config / openclaw")
- **Semantic edges** — Lines connect similar ideas (cosine similarity ≥ 0.45)

### Quick Commands

**Build brain data:**
```bash
cd /home/node/.openclaw/workspace/tools/memory-dashboard
python3 build_graph.py
```

**Serve visualization:**
```bash
python3 -m http.server 9090 --bind 0.0.0.0
```

**Access via Tailscale:**
```
http://koc-server.tailc2d84b.ts.net:9090/brain.html
```

### How It Works

**Data Pipeline:**
1. **Scan** — Read all MD files from workspace (MEMORY.md, skills/, sessions/)
2. **Chunk** — Split files by `##` and `###` headers
3. **Embed** — Match chunks to QMD's Gemma 300M embeddings (768-dim), fallback to TF-IDF
4. **Project** — UMAP 3D projection preserves semantic relationships
5. **Cluster** — OPTICS density-based clustering groups related concepts
6. **Label** — Analyze cluster content, generate 2-4 word human labels
7. **Edge** — KNN connects each node to 3 most similar neighbors

**Automation:**
- **Cron 1:** "Rebuild brain data" — 11:30 PM UTC nightly
- **Cron 2:** "Label brain clusters" — 12:05 AM UTC (35 min after build)
- Together: Fresh brain data every night with readable cluster labels

### Output Files

| File | Purpose |
|-------|----------|
| `graph_data.json` | Latest snapshot (335 nodes, 72 clusters) |
| `brain.html` | 3D interactive visualization (Three.js) |
| `snapshots/YYYY-MM-DD.json` | Daily archives for history view |

### Dashboard Features

- **3D visualization** — Rotate, zoom, pan through brain
- **Hover** — Preview memory chunk content
- **Click** — Inspect full text, metadata
- **Search** — Filter by title or content
- **Filter by type** — Lesson, daily, skill, session
- **Cluster view** — See which concepts group together
- **History** — Compare snapshots over time

### Why This Matters

This lets Anastasia **see patterns** she wouldn't notice reading text files:
- Timezone lessons cluster together → Should remember this better
- Discord config issues form a group → Recurring technical theme
- Morning greeting patterns emerge → Daily ritual visualization

It's her brain, externalized. 🥀
