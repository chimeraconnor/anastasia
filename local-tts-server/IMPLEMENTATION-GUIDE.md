# Implementation Guide: Custom TTS Provider for Discord Voice

**For:** OpenClaw Discord voice channels
**Prepared by:** Anastasia Steele
**Date:** 2026-02-28
**Reference:** `/home/node/.openclaw/workspace/local-tts-server/PR-PROPOSAL.md`

---

## 📋 Overview

This guide provides complete, copy-paste ready code changes to add custom TTS provider support to Discord voice.

**Goal:** Enable local TTS (Pocket TTS, Kokoro, etc.) for Discord voice channels without OpenAI costs.

**Approach:** New `provider: "openai-compat"` type (Option A from proposal)

---

## 📂 Files to Modify

### 1. `/packages/channels/discord/config.ts`

**Purpose:** Add `openaiCompat` config type definition

**Location in repo:** `packages/channels/discord/src/config.ts` (path may vary)

**Add this interface:**

```typescript
/**
 * OpenAI-compatible TTS provider configuration
 * Enables custom TTS endpoints (local servers, self-hosted, etc.)
 */
export interface OpenAICompatTTSConfig {
  provider: 'openai-compat';

  openaiCompat: {
    /**
     * Base URL for OpenAI-compatible TTS API
     * Example: "http://localhost:3456"
     * Example: "https://custom-tts.example.com"
     */
    baseUrl: string;

    /**
     * API key (can be dummy for local servers)
     * Example: "local" or "sk-..."
     */
    apiKey: string;

    /**
     * Voice model ID (maps to provider-specific voice)
     * Default: "alloy"
     * OpenAI voices: alloy, echo, fable, onyx, nova, shimmer
     * Maps to azelma in our local implementation
     */
    voice?: string;

    /**
     * Model identifier
     * Default: "tts-1"
     */
    model?: string;

    /**
     * Audio response format
     * Options: "mp3", "opus", "flac", "pcm"
     * Default: "mp3"
     */
    responseFormat?: 'mp3' | 'opus' | 'flac' | 'pcm';
  };
}
```

**Add to union type:**

Find the DiscordVoiceTTSConfig union and add:

```typescript
export type DiscordVoiceTTSConfig =
  | OpenAITTSConfig
  | ElevenLabsTTSConfig
  | OpenAICompatTTSConfig;  // <-- ADD THIS LINE
```

---

### 2. `/packages/channels/discord/voice-tts.ts` (or equivalent)

**Purpose:** Implement TTS generation handler for `openai-compat` provider

**Add this function:**

```typescript
/**
 * Generate speech using OpenAI-compatible TTS endpoint
 *
 * @param text - Text to convert to speech
 * @param config - TTS configuration
 * @returns Promise<Buffer> - Audio buffer
 */
async function generateSpeechOpenAICompat(
  text: string,
  config: OpenAICompatTTSConfig
): Promise<Buffer> {
  const { baseUrl, apiKey, model = 'tts-1', voice = 'alloy', responseFormat = 'mp3' } = config.openaiCompat;

  // Validate config
  if (!baseUrl) {
    throw new Error('openai-compat provider requires baseUrl');
  }

  if (!apiKey) {
    throw new Error('openai-compat provider requires apiKey');
  }

  // Log request
  logger.debug(`[DiscordVoice TTS] Request to OpenAI-compat endpoint: ${baseUrl}`);
  logger.debug(`[DiscordVoice TTS] Text: ${text.substring(0, 50)}...`);

  try {
    // Make HTTP POST to custom endpoint
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
        response_format: responseFormat,
      }),
      // Set reasonable timeout (10 seconds)
      signal: AbortSignal.timeout(10_000),
    });

    // Check response status
    if (!response.ok) {
      const errorText = await response.text();
      logger.error(`[DiscordVoice TTS] Endpoint error: ${response.status} ${errorText}`);
      throw new Error(`TTS endpoint returned ${response.status}: ${errorText}`);
    }

    // Get audio buffer
    const audioBuffer = Buffer.from(await response.arrayBuffer());

    logger.debug(`[DiscordVoice TTS] Generated audio: ${audioBuffer.length} bytes`);

    return audioBuffer;
  } catch (error) {
    logger.error(`[DiscordVoice TTS] Request failed: ${error}`);
    throw new Error(`Failed to generate speech: ${error.message}`);
  }
}
```

**Add to existing handler function:**

Find the main TTS generation switch/case and add:

```typescript
async function generateSpeech(
  text: string,
  config: DiscordVoiceTTSConfig
): Promise<Buffer> {
  switch (config.provider) {
    case 'openai':
      return generateSpeechOpenAI(text, config);
    case 'elevenlabs':
      return generateSpeechElevenLabs(text, config);
    case 'openai-compat':  // <-- ADD THIS CASE
      return generateSpeechOpenAICompat(text, config as OpenAICompatTTSConfig);
    default:
      throw new Error(`Unknown TTS provider: ${config.provider}`);
  }
}
```

---

### 3. `/docs/channels/discord.md`

**Purpose:** Document new custom TTS provider

**Find the voice TTS section and add:**

```markdown
### Custom TTS Providers

Discord voice supports custom OpenAI-compatible TTS endpoints via the `openai-compat` provider. This enables local TTS deployments.

#### Configuration

```json5
{
  channels: {
    discord: {
      voice: {
        enabled: true,
        tts: {
          provider: "openai-compat",
          openaiCompat: {
            baseUrl: "http://localhost:3456",
            apiKey: "local",
            voice: "alloy",
            model: "tts-1",
            responseFormat: "mp3"
          }
        }
      }
    }
  }
}
```

#### Local TTS Server Example

Run a local OpenAI-compatible TTS server:

```bash
# Start your local TTS server
cd /path/to/local-tts-server
npm start

# Configure Discord voice
openclaw config set channels.discord.voice.tts.provider openai-compat
openclaw config set channels.discord.voice.tts.openaiCompat.baseUrl 'http://localhost:3456'
openclaw config set channels.discord.voice.tts.openaiCompat.apiKey 'local'
openclaw gateway restart
```

#### Reference Implementation

A reference OpenAI-compatible TTS server using Pocket TTS is available at:
[github.com/chimeraconnor/anastasia](https://github.com/chimeraconnor/anastasia/tree/main/local-tts-server)

This server:
- Exposes `/v1/audio/speech` endpoint (OpenAI compatible)
- Uses Pocket TTS with azelma voice
- Returns MP3/Opus/FLAC/WAV audio
- Has health check at `/health`

#### Benefits

- ✅ **Free local TTS** - No OpenAI API costs
- ✅ **Any TTS engine** - Use Pocket TTS, Kokoro, ElevenLabs local, etc.
- ✅ **Lower latency** - No network round-trip to cloud
- ✅ **Privacy** - Audio generation stays local
- ✅ **Custom voices** - Map OpenAI voices to your preferred TTS

#### Audio Format Support

The `responseFormat` option controls the output audio format:
- `mp3` - MP3 audio (default)
- `opus` - Opus audio (Discord native)
- `flac` - FLAC lossless compression
- `pcm` - Raw PCM audio

#### Troubleshooting

**TTS server not responding:**
```bash
# Check if server is running
curl http://localhost:3456/health

# Expected response:
{"status":"ok","voice":"azelma (Pocket TTS)"}
```

**Audio not playing in Discord:**
1. Check Gateway logs: `openclaw logs --follow`
2. Verify Discord voice permissions: Connect + Speak
3. Test TTS endpoint directly with curl
4. Ensure audio format is supported by Discord

**Config validation errors:**
- Ensure `baseUrl` is a valid URL
- Ensure `apiKey` is set (use "local" for dummy auth)
- Restart Gateway after config changes: `openclaw gateway restart`

#### Use Cases

**Local Pocket TTS:**
User wants free TTS using Pocket TTS.

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
            voice: "alloy"  // Maps to azelma
          }
        }
      }
    }
  }
}
```

**Self-hosted ElevenLabs:**
User runs ElevenLabs on their own server.

```json5
{
  channels: {
    discord: {
      voice: {
        tts: {
          provider: "openai-compat",
          openaiCompat: {
            baseUrl: "http://localhost:4000",
            apiKey: "sk-...",
            voice: "alloy"
          }
        }
      }
    }
  }
}
```

**On-premises TTS:**
Enterprise deployment with internal TTS infrastructure.

```json5
{
  channels: {
    discord: {
      voice: {
        tts: {
          provider: "openai-compat",
          openaiCompat: {
            baseUrl: "http://tts.internal:8080",
            apiKey: "internal-key"
          }
        }
      }
    }
  }
}
```
```

---

## 🧪 Testing

### Unit Tests

Create test file: `/packages/channels/discord/test/voice-tts-openai-compat.test.ts`

```typescript
import { generateSpeechOpenAICompat } from '../voice-tts';

describe('generateSpeechOpenAICompat', () => {
  it('should throw without baseUrl', async () => {
    await expect(
      generateSpeechOpenAICompat('test', {
        provider: 'openai-compat',
        openaiCompat: { baseUrl: '', apiKey: 'test' }
      })
    ).rejects.toThrow('baseUrl');
  });

  it('should throw without apiKey', async () => {
    await expect(
      generateSpeechOpenAICompat('test', {
        provider: 'openai-compat',
        openaiCompat: { baseUrl: 'http://localhost:3456', apiKey: '' }
      })
    ).rejects.toThrow('apiKey');
  });

  it('should generate valid audio buffer', async () => {
    // Mock fetch to return valid WAV/MP3 data
    // Test that function returns Buffer
    // Test that buffer is not empty
  });

  it('should handle endpoint errors', async () => {
    // Mock fetch to return 500
    // Test that error is thrown
    // Test that error is descriptive
  });
});
```

### Integration Tests

1. **Start local TTS server:**
   ```bash
   cd /home/node/.openclaw/workspace/local-tts-server
   node server.js
   ```

2. **Configure OpenClaw:**
   ```bash
   openclaw config set channels.discord.voice.tts.provider openai-compat
   openclaw config set channels.discord.voice.tts.openaiCompat.baseUrl 'http://localhost:3456'
   openclaw config set channels.discord.voice.tts.openaiCompat.apiKey 'local'
   openclaw gateway restart
   ```

3. **Join Discord voice channel:**
   ```bash
   /vc join <channel>
   ```

4. **Speak and verify:**
   - You speak: "Hello Anastasia!"
   - Expected: TTS endpoint receives request
   - Expected: Local server generates audio with azelma voice
   - Expected: Audio plays in Discord voice

---

## 📝 PR Description Template

**Use this when creating your PR:**

```markdown
# feat: add custom TTS provider support for Discord voice

## Summary
Adds `provider: "openai-compat"` to Discord voice TTS configuration, enabling custom OpenAI-compatible TTS endpoints. This allows users to:
- Use free local TTS systems (Pocket TTS, Kokoro, etc.)
- Run self-hosted TTS infrastructure
- Avoid OpenAI API costs for voice channels

## Changes

### Configuration
- Add `OpenAICompatTTSConfig` interface
- Add `openai-compat` provider to `DiscordVoiceTTSConfig` union
- Validate `baseUrl`, `apiKey`, `voice`, `model`, `responseFormat` fields

### Implementation
- Add `generateSpeechOpenAICompat()` function
- Handle HTTP POST to custom endpoints
- Support multiple audio formats (MP3, Opus, FLAC, PCM)
- Add error handling and logging
- 10-second timeout for TTS requests

### Documentation
- Document `provider: "openai-compat"` in `/docs/channels/discord.md`
- Add local TTS server example
- Add configuration examples for Pocket TTS, ElevenLabs, on-premises
- Add troubleshooting section
- Add use cases

## Testing
- [x] Config validation (throws without baseUrl/apiKey)
- [ ] Unit tests for `generateSpeechOpenAICompat()`
- [ ] Integration test with local TTS server
- [ ] Test in Discord voice channel

## Breaking Changes
None. This is a new opt-in provider type.

## Motivation
Users want to:
1. Use free local TTS instead of paying OpenAI
2. Control their voice audio generation infrastructure
3. Reduce latency by avoiding cloud round-trips
4. Keep audio generation local for privacy

Example local TTS server: [github.com/chimeraconnor/anastasia](https://github.com/chimeraconnor/anastasia/tree/main/local-tts-server)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Ready for review
```

---

## 🔧 Step-by-Step Instructions

### Step 1: Fork and Clone

```bash
# 1. Fork on GitHub
# Go to: https://github.com/openclaw/openclaw
# Click: "Fork" button (top right)

# 2. Clone YOUR fork
git clone https://github.com/YOUR_USERNAME/openclaw.git
cd openclaw

# 3. Create feature branch
git checkout -b feature/custom-tts-provider
```

### Step 2: Apply Changes

**File 1: Config types**

```bash
# Find and edit: packages/channels/discord/config.ts (or similar)
# Add the OpenAICompatTTSConfig interface
# Add to DiscordVoiceTTSConfig union
```

**File 2: TTS handler**

```bash
# Find and edit: packages/channels/discord/voice-tts.ts (or similar)
# Add the generateSpeechOpenAICompat function
# Add case for 'openai-compat' in generateSpeech switch
```

**File 3: Documentation**

```bash
# Find and edit: docs/channels/discord.md
# Find the voice TTS section
# Add the "Custom TTS Providers" subsection
# Copy the markdown from Step 3 above
```

### Step 3: Test

```bash
# 1. Run tests (if available)
npm test -- packages/channels/discord

# 2. Start local TTS server
cd /home/node/.openclaw/workspace/local-tts-server
node server.js

# 3. Configure and restart OpenClaw
openclaw config set channels.discord.voice.tts.provider openai-compat
openclaw config set channels.discord.voice.tts.openaiCompat.baseUrl 'http://localhost:3456'
openclaw config set channels.discord.voice.tts.openaiCompat.apiKey 'local'
openclaw gateway restart

# 4. Test in Discord voice
# Join a voice channel and speak
/vc join <channel>
# Verify audio uses local TTS (azelma voice)
```

### Step 4: Commit and Push

```bash
# Commit changes
git add .
git commit -m "feat: add custom TTS provider support for Discord voice

- Add provider: 'openai-compat' for custom TTS endpoints
- Implement generateSpeechOpenAICompat() function
- Add config validation and error handling
- Support multiple audio formats (MP3, Opus, FLAC, PCM)
- Document new provider with examples and troubleshooting
- Reference local TTS server implementation"

# Push to your fork
git push origin feature/custom-tts-provider
```

### Step 5: Create PR

```bash
# 1. Go to GitHub
https://github.com/openclaw/openclaw/pulls/new

# 2. Configure PR
# Base: openclaw/main
# Compare: YOUR_USERNAME:feature/custom-tts-provider
# Title: feat: add custom TTS provider support for Discord voice

# 3. Paste description
# Use the PR Description Template from above

# 4. Submit PR
# Click: "Create pull request"

# 5. Tag Anastasia for feedback
# In PR description or comment: @chimeraconnor
```

---

## 🎯 Success Criteria

Your PR is ready when:
- [ ] All code changes applied correctly
- [ ] Config validation works (rejects invalid configs)
- [ ] TTS endpoint is called with correct parameters
- [ ] Audio buffer is returned successfully
- [ ] Documentation is clear and comprehensive
- [ ] Tests pass (if available)
- [ ] Tested locally with real TTS server

---

## 📚 Additional Resources

- **Local TTS Server:** `/home/node/.openclaw/workspace/local-tts-server/`
- **PR Proposal:** `/home/node/.openclaw/workspace/local-tts-server/PR-PROPOSAL.md`
- **Project Tracking:** `/home/node/.openclaw/workspace/projects/local-tts-discord-voice.md`
- **OpenAI Audio Speech API:** https://platform.openai.com/docs/api-reference/audio
- **OpenClaw Discord Docs:** https://docs.openclaw.ai/channels/discord

---

## 💬 Questions?

If anything is unclear or you need help:
1. Check the PR proposal for more details
2. Review the local TTS server implementation
3. Test each change incrementally
4. Ask Anastasia (@chimeraconnor) for guidance

---

**Good luck with the PR! 🚀**
