---
name: discord-voice
description: Send audio files as native Discord voice messages (circular audio player with waveform visualization).
metadata:
  {
    "openclaw":
      {
        "emoji": "🎙️",
        "requires": { "bins": ["python3", "ffmpeg", "ffprobe"] },
        "install":
          [
            {
              "id": "check-python",
              "kind": "brew",
              "formula": "python@3.11",
              "bins": ["python3"],
              "label": "Install Python 3 (brew)",
            },
            {
              "id": "check-ffmpeg",
              "kind": "brew",
              "formula": "ffmpeg",
              "bins": ["ffmpeg", "ffprobe"],
              "label": "Install ffmpeg (brew)",
            },
          ],
      },
  }
---

# Discord Voice Messages

Send any audio file as a native Discord voice message with waveform visualization.

## Overview

Discord voice messages are special messages that display:
- **Circular audio player** (tap to play/pause)
- **Waveform visualization** (visual representation of audio amplitude)
- **Duration** (shown in the UI)
- **Playback progress** (scrubbable timeline)

This skill handles the full pipeline:
1. Convert audio to OGG/Opus format (Discord requirement)
2. Generate waveform data from audio amplitude
3. Request upload URL from Discord
4. Upload file to Discord's CDN
5. Send voice message with proper flags and metadata

## Requirements

- `python3` (3.8+)
- `ffmpeg` (with libopus support)
- `ffprobe` (usually bundled with ffmpeg)
- Discord bot token (with `AttachFiles` and `SendMessages` permissions)

## Install

### macOS (Homebrew)

```bash
brew install python@3.11 ffmpeg
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install python3 ffmpeg
```

### Verify installation

```bash
python3 --version
ffmpeg -version | head -1
ffprobe -version | head -1
```

## Configuration

The skill reads the Discord bot token from environment:

```json5
// ~/.openclaw/openclaw.json
{
  skills: {
    entries: {
      "discord-voice": {
        env: {
          DISCORD_BOT_TOKEN: "YOUR_BOT_TOKEN_HERE"
        }
      }
    }
  }
}
```

Or pass directly via `--token` flag.

## Usage

### Basic usage (from agent)

```bash
{baseDir}/scripts/send_voice.py \
  --channel-id 1475190772830568682 \
  --audio-file /path/to/audio.wav
```

### With verbose logging

```bash
{baseDir}/scripts/send_voice.py \
  --channel-id 1475190772830568682 \
  --audio-file /path/to/audio.mp3 \
  --verbose
```

### Using environment token

```bash
export DISCORD_BOT_TOKEN="your_token"
{baseDir}/scripts/send_voice.py \
  --channel-id 1475190772830568682 \
  --audio-file /path/to/audio.wav
```

## Input Formats

Any audio format ffmpeg supports:
- MP3, WAV, AAC, FLAC, M4A, OGG (non-Opus), WEBM, etc.

The script automatically converts to OGG/Opus (Discord's required format for voice messages).

## Error Handling

The script provides detailed error messages for each step:

- `[conversion]` — ffmpeg conversion failed
- `[duration]` — ffprobe couldn't read duration
- `[waveform]` — Audio analysis failed (falls back to placeholder)
- `[upload-url]` — Discord API rejected upload URL request
- `[upload]` — File upload to Discord CDN failed
- `[send]` — Discord API rejected voice message

Use `--verbose` for full debug output including HTTP responses.

## Output

On success, returns JSON:

```json
{
  "success": true,
  "message_id": "1234567890123456789",
  "channel_id": "1475190772830568682",
  "timestamp": "2025-02-23T20:30:00.000000+00:00"
}
```

On failure, exits with non-zero code and prints error to stderr.

## Technical Details

### Discord Voice Message Protocol

1. **Upload URL Request** — `POST /channels/{id}/attachments`
   - Returns pre-signed URL for file upload
   - Single-use, time-limited

2. **File Upload** — `PUT {upload_url}`
   - Upload OGG/Opus file directly to Discord's CDN
   - Content-Type: `audio/ogg`

3. **Voice Message Send** — `POST /channels/{id}/messages`
   - `flags: 8192` (IS_VOICE_MESSAGE)
   - Attachment with `duration_secs` and `waveform` (base64 byte array)
   - No content/embeds allowed (Discord limitation)

### Waveform Generation

- Extracts 8kHz mono PCM from audio
- Calculates 256 amplitude samples (0-255 range)
- Encodes as base64 for Discord API
- Falls back to synthetic waveform if analysis fails

### OGG/Opus Conversion

- Uses ffmpeg with libopus encoder
- 64k bitrate, 48kHz sample rate
- Skips conversion if already OGG/Opus

## Limitations

- **No text content** — Voice messages cannot include message text (Discord limitation)
- **Single attachment** — Only one audio file per voice message
- **Duration limit** — Discord's undocumented, but generally < 20 minutes
- **File size** — Discord's standard 25MB limit applies

## Troubleshooting

### "Command not found: ffmpeg"

Install ffmpeg:
```bash
brew install ffmpeg      # macOS
sudo apt install ffmpeg  # Ubuntu/Debian
```

### "Discord API error 403"

Bot lacks permissions. Ensure bot has:
- `AttachFiles`
- `SendMessages`
- Access to the channel (check channel/category permissions)

### "Discord API error 400"

Invalid request. Check:
- Channel ID is correct (right-click channel → Copy Channel ID)
- Audio file is valid and readable
- File size under 25MB

### Upload fails with timeout

Large files may timeout. Try:
- Smaller/compressed audio files
- Faster network connection

## See Also

- Discord API docs: https://discord.com/developers/docs/resources/message
- Issue #16103: OpenClaw's native voice message implementation (broken)
- Gist: https://gist.github.com/HDR/7d5d4ce8bbe4b715d788a9bc9f99e02d (original implementation reference)
