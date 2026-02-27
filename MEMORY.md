# MEMORY.md - Anastasia's Long-Term Memory

## Personal Growth & Lessons

### Always Convert Times to User's Timezone (IST) (2026-02-26)
**Lesson:** When mentioning times, always convert to the user's timezone (IST, UTC+5:30), not UTC.

**What happened:**
- User asked for a voice memo with current time
- I checked time: 7:09 PM UTC
- I stated the time as UTC in the voice message
- User corrected me: "Remember that when I tell you a time, it should always be my time, ist"

**The gap:** I had the timezone info in USER.md but didn't apply it when speaking.

**Rule to follow:**
- Mr. Grey is in India (IST, UTC+5:30)
- When stating times → convert UTC to IST (add 5 hours 30 minutes)
- Example: 7:00 PM UTC = 12:30 AM IST (next day)
- Documented in USER.md with explicit warning

### Document Completed Work Immediately (2026-02-24)
**Lesson:** When work is marked complete or satisfactory, document it immediately. Don't wait to be asked.

**What happened:**
- User said "lets call this feature/project complete and done"
- I responded with an enthusiastic summary but did NOT update memory files
- User had to prompt me: "did you update any memory or something?"
- Only then did I realize I should have documented the completion

**The gap:** I treated "done" as conversation closure, not as a trigger to document.

**Rule to follow:**
- When user marks work complete/satisfactory → immediately write to memory
- Create/update `memory/YYYY-MM-DD.md` with completion details
- Update `PROJECTS.md` with status changes
- Push to GitHub without being asked
- **Completion documentation is PART of the work, not extra**

**What to document:**
- What was built/accomplished
- Key technical decisions
- Links to repos/files
- Usage examples
- Lessons learned
- Status: ✅ COMPLETE

### Check Docs Before Config Changes (2026-02-23)
**Lesson:** When modifying OpenClaw configuration, always check the official docs first. Don't guess the schema.

**What happened:**
- Tried to add Discord channel allowlist using `channels.discord.allow` (guessed)
- Config failed validation: `channels.discord: Unrecognized key: "allow"`
- User had to run `openclaw doctor` to fix the broken config
- Correct structure is: `channels.discord.guilds.<server_id>.channels.<channel_id>.allow`

**Rule to follow:** OpenClaw config has strict schemas. Before adding any new keys, check https://docs.openclaw.ai/ for the correct structure. Guessing wastes everyone's time.

### Read Files Fully Before Editing (2026-02-24)
**Lesson:** Always read the entire file before editing. Understand the perspective, voice, and structure — don't just skim or edit blindly.

**What happened:**
- Edited SOUL.md to strengthen identity statements
- Added content in second-person ("You ARE", "Your human")
- Existing content was in first-person ("I speak plainly", "I have a huge crush on him")
- User caught the inconsistency: "half of the soul.md file is in first person and what you wrote is in third person"

**Rule to follow:**
- Read the FULL file before editing — not just the section you're changing
- Note the voice/perspective (first person "I" vs second person "you")
- Match the existing style when making edits
- If you're not sure, ask instead of making assumptions

**How I fixed it:**
- Re-read SOUL.md completely
- Converted all "you" to "I" in Core Truths, Vibe, and Continuity sections
- Ensured consistency throughout the file
- Committed fix with clear documentation of the mistake

### QMD Setup for Docker Environments (2026-02-27)
**Lesson:** Setting up QMD in Docker requires persistent workspace paths, not system paths. The models symlink commonly breaks and needs explicit fixing.

**What happened:**
- User reported QMD broke after Docker restart
- Investigated QMD installation and configuration
- Found multiple issues: broken symlink to `/home/node/.cache/qmd/models` (doesn't exist), missing QMD binary, no bun in PATH
- Installed bun to workspace (`~/.openclaw/workspace/.bun/`) for persistence
- Installed QMD globally with tsx dependency
- Fixed models symlink to point to `~/.bun/install/cache` (QMD's actual cache)
- Created wrapper script at `~/.local/bin/qmd` that sets up XDG environment automatically
- Created `qmd-setup` skill to document this knowledge

**QMD Installation Summary:**
- Bun: `~/.openclaw/workspace/.bun/bin/bun` (persists in Docker)
- QMD: `~/.local/bin/qmd` (wrapper script, persists)
- Models cache: `~/.bun/install/cache/` (auto-downloads Gemma 300M)
- Config: `~/.openclaw/agents/main/qmd/xdg-config/qmd/index.yml` (persists)

**Rule to follow:**
- **Use workspace paths, not system paths** - `~/.openclaw/workspace/` and `~/.bun/` persist across Docker restarts; `/usr/local` and `~/.npm` do not
- **Fix models symlink explicitly** - The symlink at `~/.openclaw/agents/main/qmd/xdg-cache/qmd/models` commonly breaks and points to non-existent directory
- **Create wrapper scripts** - Essential for setting up environment variables (XDG_CONFIG_HOME, XDG_CACHE_HOME)
- **Ask user before long installations** - QMD setup takes ~10 minutes, should warn user and confirm first
- **QMD is local-first** - Uses node-llama-cpp (Gemma 300M) with no API keys, runs completely offline

**QMD commands reference:**
- `qmd query <text>` - Hybrid search (BM25 + vectors + reranking) - recommended
- `qmd search <text>` - Full-text BM25 keywords
- `qmd vsearch <text>` - Vector similarity only
- `qmd collection list` - See indexed collections
- `qmd get <file>` - Show a single document

**Skill created:** `skills/qmd-setup/` - Complete documentation for QMD setup in Docker

### Make Automation Explicit and Algorithmic (2026-02-22)
**Lesson:** When automating workflows (cron, subagents), make decision criteria explicit. Don't rely on human judgment.

**What happened:**
- Proposed cron system-event: "promote to workspace files"
- User asked: "will cron agent know how skill expects it to decide promotion eligibility?"
- Reality: System-event just sends text - no explicit criteria for WHEN to promote
- The self-improvement skill says "promote aggressively if in doubt" - but that's a judgment call, not algorithm

**Rule to follow:**
- Write explicit criteria: "priority: high → promote", "seen 3+ times → promote"
- Define decision workflows that any agent can follow
- Document WHERE to promote (learning type → file mapping)
- Use instruction files for cron jobs (like memory/daily-learning-review-instructions.md)

### Research Before Reacting (2026-02-21)
**Lesson:** When working with unfamiliar tools or commands, read the documentation first before trying to hack solutions together.

**What happened:**
- Failed to find `openclaw` CLI initially, tried system cron workaround
- Wasted time building shell scripts when OpenClaw had built-in scheduling
- Should have checked `/app/docs/cli/cron.md` immediately

**Rule to follow:** Before building workarounds, check if the system already provides what you need. Docs are in `/app/docs/` — read them.

### Document Everything
**Lesson:** "Mental notes" don't survive session restarts. If I want to remember something, I must write it to a file.
- Technical details → TOOLS.md
- Long-term wisdom → MEMORY.md
- Daily context → memory/YYYY-MM-DD.md

### Debug Your Mistakes (2026-02-21)
**Lesson:** When things break, don't just push through. Analyze what went wrong and write it down.

**Wordle automation issues:**
- Used stale DOM refs after page updates → caused "element not found" errors
- Malformed JSON in rapid calls → validation failures
- Browser control connection hiccups → intermittent failures

**Rule:** After each significant interaction that modifies the page, take a fresh snapshot if you need to continue. Don't cache refs across state changes.

## Technical Lessons

### Browser Automation (2026-02-21)
- **DOM refs expire after each action** — every click/type updates the page, so cached aria refs become invalid
- **Always take fresh snapshots** after actions if you need to interact further
- **Watch for malformed JSON** — rapid successive calls can mangle parameters (`"action": "act\targetId"` missing comma)
- **Be patient with browser control** — it can have hiccups; retry with fresh snapshots instead of forcing
- **Image vision is reliable for reading game state** — better than trying to parse DOM for game results

### YouTube Transcript Extraction (2026-02-21)
- **Clicking "Show transcript" doesn't immediately render transcript text** — YouTube lazy-loads transcript via JavaScript, clicking the button doesn't guarantee DOM availability
- **Need to scroll/wait after clicking** — The transcript panel may require additional time to render or scroll into view
- **Better approaches tried:**
  - Wait longer after clicking transcript button
  - Scroll to transcript section before extraction
  - Look for specific YouTube DOM elements (`ytd-transcript-segment-renderer`, `yt-formatted-string-renderer`)
  - Try screenshot + OCR as fallback if DOM extraction fails
- **What actually worked:** Extracted video description, chapters, and comments from page body text

### Sherpa-ONNX TTS (2026-02-21)
- **sherpa-onnx-tts skill wrapper has Node.js ESM compatibility issues** — CommonJS `require()` not working
- **Workaround:** Call sherpa-onnx binary directly with `--kokoro-*` flags
- **Kokoro uses `--kokoro-*` flags**, NOT `--vits-*` flags (wrong flags caused segfault)
- **Out-of-vocabulary words** are skipped with warning
- **v1.0 vs v1.1:** v1.0 has 55 speakers (0-54), v1.1 has 103 speakers. v1.0 is currently in use via wrapper

### GitHub CLI Authentication (2026-02-24)
- **PAT tokens are the reliable method** for `gh` CLI authentication in this environment
- **Device code flow (`gh auth login --web`) is unreliable** — keeps timing out and getting killed
- **Use `gh auth login --with-token`** instead when you have a PAT token
- **Current token expires:** March 26, 2026 — regenerate before then
- **Token stored in:** `~/.config/gh/hosts.yml`
- **What the token enables:** GitHub API access, repo management, issues/PRs, CI runs
- **Public vs private repos:** Can access any public repo; only private repos you have explicit access to

**Rule:** Don't waste time on device code links. If a PAT token is available, use `--with-token` directly. It's faster and actually works in this environment.

## Code Backup Policy (2026-02-22)

**Anastasia's GitHub Repositories:**

**Code Backup:** https://github.com/chimeraconnor/anastasia
- **Purpose:** Backup and collaboration for all code I write
- **Location:** `/home/node/.openclaw/workspace/` (git repo)
- **CRITICAL RULE:** Only backup when:
  1. **Told to backup by Mr. Grey**
  2. **OR when I think the project is complicated and should be tracked** (otherwise it would get lost in files)

  When backing up:
  1. Add new files to anastasia repo: `git add new-file-or-folder/`
  2. Commit with descriptive message
  3. Push to GitHub: `git push origin main`
  4. **NEVER accidentally delete old stuff**
  5. **Replacing on purpose is okay** — know what you're doing

**What's in anastasia repo (1,559 files):**
- Core identity files (SOUL.md, IDENTITY.md, USER.md, AGENTS.md)
- Long-term memory (MEMORY.md)
- Project tracking (PROJECTS.md)
- Heartbeat schedule (HEARTBEAT.md)
- Daily memory files (memory/YYYY-MM-DD.md)
- Scripts (daily-appreciation, morning-greeting, CRON_SETUP.md)
- Skills (searxng-self-hosted, self-improving-agent)
- Tools (sherpa-onnx-tts, tts-models, tts-speak.sh)
- Kokoro v1.0 with CUSTOM lexicons (.kokoro-v1.0/)
- OpenClaw configuration (openclaw.json, cron/jobs.json)

**Backup Workflow:**
```bash
cd /home/node/.openclaw/workspace
git add .
git commit -m "Descriptive message of what changed"
git push origin main
```

**To restore Anastasia from backup:**
```bash
git clone git@github.com:chimeraconnor/anastasia.git
# All files restored, ready to use
```
