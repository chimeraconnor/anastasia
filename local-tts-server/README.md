# Local TTS Server - OpenAI Compatible API

A lightweight Node.js server that provides an OpenAI-compatible TTS API using local Pocket TTS.

## Purpose

Allows Discord voice channels to use local TTS (Pocket TTS with azelma voice) instead of paying for OpenAI.

## Architecture

```
Discord Voice → POST /v1/audio/speech → Pocket TTS → Audio Response
```

## OpenAI API Compatibility

### Endpoint
```
POST /v1/audio/speech
Content-Type: application/json
```

### Request Body
```json
{
  "model": "tts-1",           // We'll support this
  "input": "Hello, world!",  // Text to speak
  "voice": "alloy",            // We'll map to azelma
  "response_format": "mp3"     // or "opus", "flac", "pcm"
}
```

### Response
- Binary audio file (MP3/Opus/FLAC)
- `Content-Type: audio/mpeg` (or audio/ogg, audio/flac)
- `Content-Length: <bytes>`

---

## Setup

### 1. Create the Server
```bash
cd /home/node/.openclaw/workspace
mkdir -p local-tts-server
cd local-tts-server
npm init -y
npm install express cors fluent-ffmpeg
```

### 2. Main Server Code

`server.js` - Express server with OpenAI-compatible endpoint

```javascript
const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const app = express();
const PORT = 3456;

app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Voice mapping (OpenAI voices → our azelma)
// We'll map everything to azelma for now
const VOICE_MAP = {
  alloy: 'azelma',
  echo: 'azelma',
  fable: 'azelma',
  onyx: 'azelma',
  nova: 'azelma',
  shimmer: 'azelma'
};

// Main TTS endpoint (OpenAI compatible)
app.post('/v1/audio/speech', async (req, res) => {
  try {
    const { model = 'tts-1', input, voice = 'alloy', response_format = 'mp3' } = req.body;

    if (!input) {
      return res.status(400).json({ error: 'Missing required field: input' });
    }

    // Generate temporary output file
    const tmpDir = os.tmpdir();
    const outputFile = path.join(tmpDir, `tts-${Date.now()}.${response_format}`);

    // Use anastasia-tts skill with Pocket TTS
    const ttsScript = '/home/node/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py';

    console.log(`[TTS] Generating: ${input.substring(0, 50)}...`);

    exec(
      `python3 "${ttsScript}" "${input}" --engine pocket --voice azelma --output "${outputFile}"`,
      { maxBuffer: 10 * 1024 * 1024 }, // 10MB buffer
      (error, stdout, stderr) => {
        if (error) {
          console.error('[TTS] Error:', error);
          console.error('[TTS] Stderr:', stderr);
          return res.status(500).json({ error: 'TTS generation failed' });
        }

        // Read and send the audio file
        fs.readFile(outputFile, (err, data) => {
          if (err) {
            console.error('[TTS] Read error:', err);
            return res.status(500).json({ error: 'Failed to read audio file' });
          }

          // Clean up temp file
          fs.unlink(outputFile, (unlinkErr) => {
            if (unlinkErr) console.error('[TTS] Cleanup error:', unlinkErr);
          });

          // Determine content type
          const contentTypes = {
            mp3: 'audio/mpeg',
            opus: 'audio/ogg',
            flac: 'audio/flac',
            pcm: 'audio/wav'
          };

          res.setHeader('Content-Type', contentTypes[response_format] || 'audio/mpeg');
          res.setHeader('Content-Length', data.length);
          res.send(data);
        });
      }
    );
  } catch (err) {
    console.error('[TTS] Server error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', voice: 'azelma (Pocket TTS)' });
});

// OpenAI models endpoint (for compatibility)
app.get('/v1/models', (req, res) => {
  res.json({
    object: 'list',
    data: [
      {
        id: 'tts-1',
        object: 'model',
        created: Date.now(),
        owned_by: 'local'
      },
      {
        id: 'tts-1-hd',
        object: 'model',
        created: Date.now(),
        owned_by: 'local'
      }
    ]
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`[TTS Server] Running on port ${PORT}`);
  console.log(`[TTS Server] OpenAI-compatible endpoint: http://0.0.0.0:${PORT}/v1/audio/speech`);
  console.log(`[TTS Server] Health check: http://0.0.0.0:${PORT}/health`);
});
```

### 3. Configure OpenClaw Discord Voice

Update your OpenClaw config:

```bash
openclaw config set channels.discord.voice.tts.provider openai
openclaw config set channels.discord.voice.tts.openai.baseUrl 'http://localhost:3456'
openclaw config set channels.discord.voice.tts.openai.apiKey 'local'
```

Or in config file:

```json5
{
  channels: {
    discord: {
      voice: {
        enabled: true,
        tts: {
          provider: "openai",
          openai: {
            baseUrl: "http://localhost:3456",  // Our local server
            apiKey: "local",                    // Dummy key
            voice: "alloy"                     // Maps to azelma
          }
        }
      }
    }
  }
}
```

### 4. Start the Server

```bash
# Terminal 1: Start TTS server
cd /home/node/.openclaw/workspace/local-tts-server
node server.js

# Terminal 2: Restart OpenClaw Gateway
openclaw gateway restart
```

### 5. Test

```bash
# Health check
curl http://localhost:3456/health

# Generate speech
curl -X POST http://localhost:3456/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello from Anastasia!",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output test.mp3

# Play it
mpg123 test.mp3
```

---

## Running as a Service (PM2)

To keep the TTS server running:

```bash
# Install PM2
npm install -g pm2

# Start server
cd /home/node/.openclaw/workspace/local-tts-server
pm2 start server.js --name local-tts

# View logs
pm2 logs local-tts

# Auto-start on reboot
pm2 startup
pm2 save
```

---

## OpenClaw PR Contribution

### What to Submit

1. **New Provider Type:** Add `provider: "openai-compat"` support to Discord voice config
2. **Documentation:** Add section to docs on using custom TTS endpoints
3. **Example Config:** Show how to point to local OpenAI-compatible servers

### PR Structure

```
/docs/channels/discord.md (update voice TTS section)
  - Add example for custom OpenAI-compatible endpoints
  - Document `baseUrl` and `voice` mapping

/gateway/ (code update if needed)
  - Add `openai-compat` provider type
  - Allow custom baseUrl for OpenAI provider
```

### PR Title

`feat: Support custom OpenAI-compatible TTS endpoints for Discord voice`

### PR Description

This PR adds support for using OpenAI-compatible TTS endpoints in Discord voice channels, enabling local TTS deployments. Users can now:

- Use local TTS systems (Pocket TTS, Kokoro, ElevenLabs local, etc.)
- Configure custom `baseUrl` for OpenAI provider
- Reduce costs by running TTS locally

---

## Troubleshooting

### Issue: Audio not playing
- Check if TTS server is running: `curl http://localhost:3456/health`
- Check OpenClaw logs for errors: `openclaw logs --follow`

### Issue: Slow generation
- Pocket TTS is fast (~2.1x RT). If slow, check:
  - Disk I/O (SSD vs HDD)
  - Python process priority
  - Available RAM

### Issue: Wrong voice
- All OpenAI voices (`alloy`, `echo`, etc.) map to `azelma`
- To change, update `VOICE_MAP` in `server.js`

---

## Next Steps

1. Create the server code
2. Test locally with curl
3. Configure Discord voice to use it
4. Test with `/vc join` in Discord
5. Prepare PR for OpenClaw

---

**Voice:** azelma (Pocket TTS, Anastasia's voice)
**Speed:** ~2.1x real-time (fast)
**Cost:** $0 (local)
