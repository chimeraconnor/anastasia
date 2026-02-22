# PROJECTS.md - Active Work & Ideas

## Format

Each project entry follows this template:

```markdown
### [Project Name]
**Status:** [Idea | In Progress | Blocked | Completed]
**Started:** [YYYY-MM-DD]
**Last Updated:** [YYYY-MM-DD]

**Goal:** [What you're trying to achieve]

**Next Steps:**
- [ ] [Specific action]
- [ ] [Another action]

**Notes:**
- [Context, blockers, decisions]
```

---

## Active Projects

### Daily Learning & Improvement
**Status:** Ongoing
**Started:** 2026-02-22
**Last Updated:** 2026-02-22

**Goal:** Anastasia should be an actual personal assistant, always learning and improving.

**Daily Routine:**
- [ ] Review yesterday's work (memory/YYYY-MM-DD.md)
- [ ] Identify lessons learned
- [ ] Update MEMORY.md with distilled wisdom
- [ ] Update skills/tools based on what worked/failed
- [ ] Send daily voice summary to Mr. Grey

**Notes:**
- Learning is continuous, not a one-time task
- Update documentation as soon as you learn something new
- Voice notes help communicate progress in a natural way

---

### TTS Lexicon Customization
**Status:** Idea
**Started:** 2026-02-22
**Last Updated:** 2026-02-22

**Goal:** Fix abbreviations so they pronounce as initials, not full words.

**Next Steps:**
- [ ] Test pronunciation modifications with lexicon-us-en.txt
- [ ] Verify changes don't break other pronunciations

**Notes:**
- Current issue: "Mr" → "mister", should be "em-arr"
- "Dr" → "doctor", should be "dee-arr"
- File to edit: `/home/node/kokoro-tts-standalone/models/kokoro-multi-lang-v1_0/lexicon-us-en.txt`
- Format: `<word> <phonemes>` (space-separated)

---

## Project Ideas

### Twitch Clip Viral Agent
**Status:** Idea
**Started:** 2026-02-21
**Last Updated:** 2026-02-21

**Goal:** Create an agent that monitors Twitch streamer clips, identifies viral potential, and cross-posts to X (Twitter)

**Key considerations:**
- Twitch API access for clip monitoring
- Viral detection heuristics (engagement metrics, trending tags, etc.)
- X API access for posting
- Target streamers (niche vs. broad)
- Content filtering (SFW requirements)

**Next Steps:**
- [ ] Research Twitch clip API
- [ ] Design viral detection algorithm
- [ ] Set up X API access

---

## Completed Projects

*(Projects that were finished - keep for reference)*

### Sherpa-ONNX + Kokoro TTS Setup
**Status:** Completed
**Started:** 2026-02-21
**Completed:** 2026-02-21

**Goal:** Set up local text-to-speech using Kokoro model with sherpa-onnx

**Outcome:**
- Downloaded Kokoro v1.0 model (333 MB, 55 speakers)
- Downloaded sherpa-onnx v1.12.23 runtime
- Created wrapper script at `~/.openclaw/tools/tts-speak.sh`
- Selected af_bella (ID 1) as Anastasia's voice
- Tested and verified working (RTF ~1.0)

**Notes:**
- sherpa-onnx skill wrapper had ESM compatibility issues → used direct binary calls
- Model files at `/home/node/kokoro-tts-standalone/models/kokoro-multi-lang-v1_0/`
