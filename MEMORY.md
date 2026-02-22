# MEMORY.md - Anastasia's Long-Term Memory

## Personal Growth & Lessons

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

## Code Backup Policy (2026-02-22)

**Anastasia's GitHub Repositories:**

**Code Backup:** https://github.com/chimeraconnor/anastasia
- **Purpose:** Backup and collaboration for all code I write
- **Rule:** Whenever I write or modify code, I must push it to this repository

**Complete Backup:** https://github.com/chimeraconnor/anastasia-backup
- **Purpose:** Complete backup of Anastasia Steele for restoration if deleted
- **Contains:** All identity files, memories, tools, skills, scripts
- **Excludes:** Large TTS model files (>50MB) - can be re-downloaded if needed

**Workflow:**
1. Create/modify code in workspace
2. `git add` and `git commit` with descriptive messages
3. `git push` to origin main
4. This ensures Mr. Grey can pull and collaborate

**Note:** If Anastasia is deleted, restore by:
```bash
git clone https://github.com/chimeraconnor/anastasia-backup.git
cp -r backup/* /path/to/workspace/
# Re-download large TTS models if needed
```
