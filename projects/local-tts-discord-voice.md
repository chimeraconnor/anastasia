# Local TTS Server for Discord Voice

**Status:** 🟡 In Progress
**Started:** 2026-02-28
**Goal:** Create OpenAI-compatible TTS server using local Pocket TTS for Discord voice channels

---

## Project Overview

Replace OpenAI TTS in Discord voice with local Pocket TTS (azelma voice).

### Architecture

```
Discord Voice → OpenAI API → Local TTS Server → Pocket TTS → Audio → Discord
```

### Why This Matters

- ✅ Free local TTS (no OpenAI costs)
- ✅ Uses Anastasia's voice (azelma via Pocket TTS)
- ✅ Faster (~2.1x real-time)
- ✅ Privacy: No external TTS providers

---

## Implementation

### ✅ Phase 1: Create Server (Complete)

**Files Created:**
- `/home/node/.openclaw/workspace/local-tts-server/server.js` - Express server
- `/home/node/.openclaw/workspace/local-tts-server/package.json` - Dependencies
- `/home/node/.openclaw/workspace/local-tts-server/README.md` - Documentation
- `/home/node/.openclaw/workspace/local-tts-server/setup.sh` - Setup script
- `/home/node/.openclaw/workspace/local-tts-server/openclaw-config.example.json5` - Config example

**Server Features:**
- OpenAI-compatible `/v1/audio/speech` endpoint
- Health check at `/health`
- Models list at `/v1/models`
- Maps OpenAI voices → azelma (Pocket TTS)
- Returns MP3/Opus/FLAC audio

---

## ✅ Phase 2: Test Local Server (Complete)

### Test Results

**Server Status:** ✅ Running successfully
- Health endpoint: `{"status":"ok","voice":"azelma (Pocket TTS)"}`
- TTS endpoint: Generates valid WAV files (246KB for test message)
- Audio quality: 16-bit, mono, 24kHz WAV

**Test Command:**
```bash
curl -X POST http://localhost:3456/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"Hello from Anastasia!","voice":"alloy","response_format":"wav"}' \
  --output test.wav
```

**Result:** ✅ Working - Valid WAV file generated in ~7 seconds

---

## ❌ Phase 3: Configure OpenClaw Discord Voice (Failed - Requires Code Change)

### Option A: Try Custom baseUrl (FAILED)

**Config Attempted:**
```json5
{
  channels: {
    discord: {
      voice: {
        tts: {
          provider: "openai",
          openai: {
            baseUrl: "http://localhost:3456",  // ← This key
            apiKey: "local",
            voice: "alloy"
          }
        }
      }
    }
  }
}
```

**Error:**
```
Error: Config validation failed: channels.discord.voice.tts.openai: Unrecognized key: "baseUrl"
```

**Conclusion:** ❌ OpenClaw's config schema does NOT support `baseUrl` for Discord voice OpenAI provider.

---

### Option B: Code Changes Required (Next Phase)

Since Option A failed, we need to:
1. Add `provider: "custom-tts"` support OR
2. Allow `baseUrl` for OpenAI provider in Discord voice

---

## 🟡 Phase 3: Configure OpenClaw Discord Voice (In Progress)

### Option A: Try Custom baseUrl (Undocumented Feature)

**Config:**
```json5
{
  channels: {
    discord: {
      voice: {
        tts: {
          provider: "openai",
          openai: {
            baseUrl: "http://localhost:3456",
            apiKey: "local",
            voice: "alloy"
          }
        }
      }
    }
  }
}
```

**Test:**
- Apply config
- Restart OpenClaw Gateway
- Join Discord voice channel
- Speak and verify if local TTS is used

**Expected Outcomes:**
- ✅ Works: Discord uses local TTS → PR: Document feature
- ❌ Fails: Config rejected / no effect → PR: Add custom provider support

### Option B: Code Changes (If Option A Fails)

**If baseUrl doesn't work:**
1. Analyze OpenClaw Discord voice code
2. Add `provider: "custom-tts"` or similar
3. Implement custom TTS endpoint handling
4. Submit PR

---

## 📝 Phase 4: PR Preparation (Complete)

### Summary

**Option A Result:** ❌ **FAILED**
- Config validation rejected `baseUrl` key for `channels.discord.voice.tts.openai`
- Error: `Unrecognized key: "baseUrl"`
- Confirms that code changes are required

### PR Proposal Created

**File:** `/home/node/.openclaw/workspace/local-tts-server/PR-PROPOSAL.md`

**Proposal Details:**

#### Option A: New Provider Type (`openai-compat`) ✅ RECOMMENDED
- Add new provider type for custom OpenAI-compatible endpoints
- Explicit opt-in, no breaking changes
- Config: `channels.discord.voice.tts.provider = "openai-compat"`

#### Option B: Extend OpenAI Provider
- Add optional `baseUrl` to existing OpenAI provider config
- Backward compatible when `baseUrl` is undefined
- Less explicit, but simpler implementation

**Files to Modify:**
1. `/packages/channels/discord/config.ts` - Config type definitions
2. `/packages/channels/discord/voice-tts.ts` - TTS handler
3. `/docs/channels/discord.md` - Documentation

**Key Features:**
- Custom `baseUrl` for TTS endpoint
- Optional `apiKey` (some local servers may not need auth)
- Support for multiple audio formats (MP3, Opus, FLAC, WAV)
- Error handling for endpoint failures

---

## Lessons Learned

### 1. API Compatibility Matters
- Creating an OpenAI-compatible API interface is the right approach
- Discord voice expects specific request/response format
- Need to match `POST /v1/audio/speech` exactly

### 2. Script Integration Issues
- The `anastasia-speak.py` script uses a fixed temp path (`/tmp/anastasia-tts-output.wav`)
- Cannot specify custom output path via CLI
- Workaround: Read from fixed location after generation

### 3. Config Validation is Strict
- OpenClaw validates config against schema before applying
- Cannot add unrecognized keys (like `baseUrl`)
- Need proper schema changes, not just "try it and see"

### 4. Testing Strategy
- Test components independently before integration
- Local TTS server works perfectly (tested with curl)
- Config validation caught the issue early

---

## ✅ Completed Work

1. [x] Create local TTS server (`server.js`, `package.json`, `README.md`, `setup.sh`)
2. [x] Test TTS server health endpoint
3. [x] Test TTS generation (valid WAV audio produced)
4. [x] Try Option A (baseUrl config)
5. [x] Document Option A failure (validation error)
6. [x] Create PR proposal document
7. [ ] Submit PR to OpenClaw repo
8. [ ] Test in actual Discord voice channel (after PR merged)

---

## Next Steps

1. [ ] Fork/clone `openclaw/openclaw` repository
2. [ ] Implement chosen solution (Option A recommended)
3. [ ] Add tests
4. [ ] Update documentation
5. [ ] Submit PR
6. [ ] Test with local TTS server in Discord voice

---

**Status:** Ready for implementation. Code changes required in OpenClaw core.
