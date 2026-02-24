# Discord Voice Message Skill

Send audio files as native Discord voice messages with waveform visualization.

## ⚠️ Important: Use This, Not Native `asVoice`

**OpenClaw's native `message(asVoice=true)` is broken (Issue #16103).** It returns generic "Error" responses even when messages send successfully.

**This skill is the recommended approach** — it implements Discord's voice message protocol directly via Python and provides reliable success/error feedback.

## Overview

Discord voice messages are special messages that display audio with a circular player, waveform visualization, duration, and playback controls. This skill implements the full Discord voice message protocol.

## Features

- ✅ **Auto-converts** any audio format to OGG/Opus
- ✅ **Generates waveform** from audio amplitude (256 samples)
- ✅ **3-step API flow** (Upload URL → File upload → Voice message send)
- ✅ **Per-step error handling** with descriptive messages
- ✅ **Auto-reads token** from OpenClaw config
- ✅ **Resource cleanup** (deletes temp files automatically)
- ✅ **Detailed logging** with `--verbose` mode

## Requirements

- Python 3.8+
- ffmpeg (with libopus support)
- ffprobe
- Discord bot token with `SendMessages` and `AttachFiles` permissions

## Installation

The skill is already installed in your workspace at `~/.openclaw/workspace/skills/discord-voice/`

### Step 1: Verify Dependencies

```bash
python3 --version
ffmpeg -version
ffprobe -version
```

### Step 2: Configure Discord Bot Token (Optional)

The skill automatically reads your Discord bot token from OpenClaw config (`channels.discord.token`). No additional configuration needed.

If you prefer, you can also set it via environment variable:
```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token_here"
```

## Usage

### Basic Usage (Recommended)

Send any audio file as a Discord voice message:

```bash
python3 ~/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py \
  --channel-id 1475190772830568682 \
  --audio-file /path/to/audio.wav
```

### With TTS Integration

Generate voice with TTS, then send as Discord voice message:

```bash
# Step 1: Generate audio
~/.openclaw/tools/tts-speak.sh "Hello Mr. Grey" /tmp/voice.wav kokoro 1

# Step 2: Send as voice message
python3 ~/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py \
  --channel-id 1475566112019058758 \
  --audio-file /tmp/voice.wav
```

### With Verbose Logging

```bash
python3 ~/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py \
  --channel-id 1475190772830568682 \
  --audio-file /path/to/audio.wav \
  --verbose
```

## Why Not Native `asVoice`?

| Feature | Native `asVoice` | This Skill |
|---------|------------------|------------|
| Error messages | Generic "Error" | Detailed per-step errors |
| Success confirmation | Unreliable | JSON response with message_id |
| Waveform generation | ✅ Yes | ✅ Yes |
| Audio conversion | ✅ Yes | ✅ Yes |
| Works reliably | ❌ No (Issue #16103) | ✅ Yes |

## Output

On success, returns JSON with message details:

```json
{
  "success": true,
  "message_id": "1475626534000922735",
  "channel_id": "1475190772830568682",
  "timestamp": "2026-02-23T22:05:54.602000+00:00"
}
```

## Error Codes

| Error Code | Description |
|------------|-------------|
| `[conversion]` | ffmpeg failed to convert audio to OGG/Opus |
| `[duration]` | ffprobe failed to get audio duration |
| `[waveform]` | Audio analysis failed (falls back to placeholder) |
| `[upload-url]` | Discord API rejected upload URL request |
| `[upload]` | File upload to Discord CDN failed |
| `[send]` | Discord API rejected voice message send |

## Troubleshooting

### "Discord API error 403" or "error code: 1010"

**Possible causes:**
- Bot lacks `SendMessages` permission
- Bot doesn't have access to channel
- Token has been reset or revoked

**Solutions:**
- Check bot permissions in Discord server settings
- Regenerate Discord bot token from [Developer Portal](https://discord.com/developers/applications)
- Ensure bot is in server and has channel access

### "Error: Discord bot token required"

The script cannot find a Discord bot token from:
- OpenClaw config (`channels.discord.token`)
- Environment variable `DISCORD_BOT_TOKEN`
- `--token` flag

**Solution:** Ensure your Discord bot token is configured in OpenClaw config.

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
- Base64 encodes for Discord API
- Falls back to sine-wave pattern if analysis fails

### OGG/Opus Conversion

- Uses ffmpeg with libopus encoder
- 64k bitrate, 48kHz sample rate
- Skips conversion if already OGG/Opus

## Development

**Author:** Anastasia Steele  
**Repository:** [chimeraconnor/anastasia](https://github.com/chimeraconnor/anastasia)  
**License:** MIT (if applicable)

---

*This skill works around OpenClaw issue #16103 — the native `asVoice` parameter in the message tool is broken. Use this skill instead.*
