const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const app = express();
const PORT = process.env.PORT || 3456;

app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Voice mapping (OpenAI voices → our azelma)
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

    // Use anastasia-tts skill with Pocket TTS
    const ttsScript = '/home/node/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py';
    const tempOutput = '/tmp/anastasia-tts-output.wav'; // Fixed temp location used by the script

    console.log(`[TTS] Generating: ${input.substring(0, 50)}...`);

    exec(
      `python3 "${ttsScript}" "${input}" --engine pocket --voice azelma`,
      { maxBuffer: 10 * 1024 * 1024 }, // 10MB buffer
      (error, stdout, stderr) => {
        if (error) {
          console.error('[TTS] Error:', error);
          console.error('[TTS] Stderr:', stderr);
          return res.status(500).json({ error: 'TTS generation failed' });
        }

        // Read and send audio file (script generates to fixed temp location)
        fs.readFile(tempOutput, (err, data) => {
          if (err) {
            console.error('[TTS] Read error:', err);
            return res.status(500).json({ error: 'Failed to read audio file' });
          }

          // Determine content type (script outputs WAV)
          const contentTypes = {
            mp3: 'audio/mpeg',
            opus: 'audio/ogg',
            flac: 'audio/flac',
            pcm: 'audio/wav',
            wav: 'audio/wav'
          };

          res.setHeader('Content-Type', contentTypes[response_format] || 'audio/wav');
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
