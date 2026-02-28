# PR Proposal: Custom TTS Provider for Discord Voice

**Status:** 🟡 Ready for Implementation
**Target Repository:** `openclaw/openclaw`
**Created:** 2026-02-28

---

## Problem Statement

Discord voice channels currently only support OpenAI and ElevenLabs for TTS via the `channels.discord.voice.tts` configuration. Users cannot:

1. Use local TTS systems (Pocket TTS, Kokoro, etc.)
2. Point to custom OpenAI-compatible endpoints
3. Avoid OpenAI API costs for voice channels

### Current Config Schema (Limited)

```json5
{
  channels: {
    discord: {
      voice: {
        tts: {
          provider: "openai",  // or "elevenlabs"
          openai: {
            voice: "alloy",
            // NO baseUrl support
            // NO custom endpoint support
          }
        }
      }
    }
  }
}
```

### Validation Error

When attempting to add `baseUrl`:
```
Error: Config validation failed: channels.discord.voice.tts.openai: Unrecognized key: "baseUrl"
```

---

## Proposed Solution

Add `provider: "openai-compat"` (or similar) to Discord voice TTS configuration, enabling custom OpenAI-compatible TTS endpoints.

### New Config Schema

```json5
{
  channels: {
    discord: {
      voice: {
        tts: {
          provider: "openai-compat",
          openaiCompat: {
            baseUrl: "http://localhost:3456",
            apiKey: "local",
            voice: "alloy",
            model: "tts-1"
          }
        }
      }
    }
  }
}
```

### Alternative: Extend Existing Provider

```json5
{
  channels: {
    discord: {
      voice: {
        tts: {
          provider: "openai",
          openai: {
            baseUrl: "http://localhost:3456",  // NEW: Support custom endpoint
            apiKey: "local",
            voice: "alloy"
          }
        }
      }
    }
  }
}
```

**Recommendation:** Use `openai-compat` provider type to:
1. Make the feature explicit and opt-in
2. Avoid breaking changes to existing OpenAI provider
3. Allow future expansion of compat providers

---

## Implementation Plan

### Option A: New Provider Type (`openai-compat`) ✅ Recommended

**Files to modify:**

1. **`/packages/channels/discord/config.ts`** (or equivalent)
   - Add `openaiCompat` config type definition
   - Validate `baseUrl`, `apiKey`, `voice`, `model` fields

2. **`/packages/channels/discord/voice-tts.ts`** (or equivalent)
   - Implement TTS handler for `openai-compat` provider
   - Make HTTP POST to custom endpoint
   - Handle audio response formats (MP3, Opus, FLAC, PCM)

3. **`/docs/channels/discord.md`**
   - Document new `provider: "openai-compat"`
   - Add example config
   - Add troubleshooting notes

**Code Changes (Pseudo):**

```typescript
// Config type
export interface OpenAICompatTTSConfig {
  provider: 'openai-compat';
  openaiCompat: {
    baseUrl: string;
    apiKey: string;
    voice?: string;
    model?: string;
  };
}

// TTS handler
async function generateSpeechOpenAICompat(
  text: string,
  config: OpenAICompatTTSConfig
): Promise<Buffer> {
  const { baseUrl, apiKey, model = 'tts-1', voice = 'alloy' } = config.openaiCompat;

  const response = await fetch(`${baseUrl}/v1/audio/speech`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      input: text,
      voice,
      response_format: 'mp3', // or get from config
    }),
  });

  return Buffer.from(await response.arrayBuffer());
}
```

### Option B: Extend OpenAI Provider

**Files to modify:**

1. **`/packages/channels/discord/config.ts`**
   - Add optional `baseUrl` to `OpenAITTSConfig`

2. **`/packages/channels/discord/voice-tts.ts`**
   - If `baseUrl` is set, use custom endpoint instead of API endpoint
   - Keep existing behavior when `baseUrl` is undefined

**Code Changes:**

```typescript
interface OpenAITTSConfig {
  provider: 'openai';
  openai: {
    baseUrl?: string;  // NEW: Optional custom endpoint
    apiKey?: string;
    voice?: string;
  };
}

async function generateSpeechOpenAI(
  text: string,
  config: OpenAITTSConfig
): Promise<Buffer> {
  const { apiKey, voice = 'alloy' } = config.openai;

  // Use custom endpoint if configured
  const baseUrl = config.openai.baseUrl || 'https://api.openai.com/v1';

  const response = await fetch(`${baseUrl}/audio/speech`, {
    // ... rest of implementation
  });
}
```

---

## Testing Plan

### Unit Tests
- [ ] Test config validation with `openai-compat` provider
- [ ] Test HTTP POST to custom endpoint
- [ ] Test audio buffer handling
- [ ] Test error handling (endpoint down, invalid response)

### Integration Tests
- [ ] Start local TTS server
- [ ] Configure Discord voice with custom endpoint
- [ ] Join Discord voice channel
- [ ] Verify audio output uses local TTS
- [ ] Test with multiple voices, formats

### Example Local TTS Server

A reference implementation is provided at:
`/home/node/.openclaw/workspace/local-tts-server/`

This server:
- Runs on port 3456
- Exposes OpenAI-compatible `/v1/audio/speech` endpoint
- Uses Pocket TTS with azelma voice
- Returns WAV audio

---

## Documentation Changes

### `/docs/channels/discord.md` Updates

Add new section:

```markdown
## Custom TTS Providers

Discord voice supports custom OpenAI-compatible TTS endpoints via the `openai-compat` provider.

### Configuration

```json5
{
  channels: {
    discord: {
      voice: {
        tts: {
          provider: "openai-compat",
          openaiCompat: {
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

### Local TTS Example

Run a local OpenAI-compatible TTS server:

```bash
# Start your local TTS server
cd /path/to/local-tts-server
npm start

# Configure Discord voice
openclaw config set channels.discord.voice.tts.provider openai-compat
openclaw config set channels.discord.voice.tts.openaiCompat.baseUrl 'http://localhost:3456'
openclaw gateway restart
```

### Benefits

- ✅ Free local TTS (no API costs)
- ✅ Use any TTS engine (Pocket, Kokoro, ElevenLabs local)
- ✅ Lower latency (no network round-trip to cloud)
- ✅ Privacy (audio stays local)
```

---

## Use Cases

### 1. Local Pocket TTS
User wants Anastasia's voice in Discord voice without OpenAI costs.

**Setup:**
```bash
# Run local TTS with Pocket TTS (azelma)
python3 local-tts-server/server.py

# Configure Discord voice
openclaw config set channels.discord.voice.tts.provider openai-compat
openclaw config set channels.discord.voice.tts.openaiCompat.baseUrl 'http://localhost:3456'
```

### 2. Self-Hosted ElevenLabs
User runs ElevenLabs locally or on their own server.

**Setup:**
```bash
# Run custom ElevenLabs server
python3 eleven-tts-server/server.py --model eleven_multilingual_v2

# Configure Discord voice
openclaw config set channels.discord.voice.tts.provider openai-compat
openclaw config set channels.discord.voice.tts.openaiCompat.baseUrl 'http://localhost:4000'
```

### 3. On-Premise TTS
Enterprise deployment with on-premises TTS infrastructure.

**Setup:**
```bash
# Point to internal TTS service
openclaw config set channels.discord.voice.tts.openaiCompat.baseUrl 'http://tts.internal:8080'
```

---

## Breaking Changes

**None** - This is a new provider type, existing configs unaffected.

---

## Migration Path

No migration needed. Users opt-in by changing provider to `openai-compat`.

---

## Questions for OpenClaw Team

1. Preferred provider name? (`openai-compat`, `custom-tts`, or other?)
2. Should we add `response_format` support to config?
3. Should `apiKey` be required or optional (some local servers may not need auth)?
4. Any additional validation or error handling recommendations?

---

## References

- Local TTS Server Implementation: `/home/node/.openclaw/workspace/local-tts-server/`
- OpenAI Audio Speech API: https://platform.openai.com/docs/api-reference/audio
- Discord Voice Documentation: `/docs/channels/discord.md`

---

## Next Steps

1. [ ] Get feedback on proposal from OpenClaw team
2. [ ] Implement chosen solution (Option A or B)
3. [ ] Add tests
4. [ ] Update documentation
5. [ ] Submit PR
6. [ ] Test with local TTS server

---

**Prepared by:** Anastasia Steele
**Date:** 2026-02-28
**Issue Reference:** Custom TTS providers for Discord voice
