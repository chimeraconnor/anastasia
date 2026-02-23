#!/bin/bash
# Discord Voice Message Usage Examples
# 
# This demonstrates how to use the discord-voice skill from OpenClaw

# === Example 1: Send a TTS-generated voice note ===

# Step 1: Generate TTS audio
tts-speak.sh "Hello Mr. Grey, this is a voice message sent via the new skill." \
  /tmp/test-voice.wav kokoro 1

# Step 2: Send as Discord voice message
python3 ~/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py \
  --channel-id 1475190772830568682 \
  --audio-file /tmp/test-voice.wav \
  --verbose

# === Example 2: Send existing audio file ===

python3 ~/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py \
  --channel-id 1475190772830568682 \
  --audio-file /path/to/your/audio.mp3

# === Example 3: Using from OpenClaw agent ===

# The agent can call this via exec tool:
# exec({
#   "command": "python3 /home/node/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py --channel-id 1475190772830568682 --audio-file /tmp/audio.wav --verbose"
# })

# === Configuration ===

# Add to ~/.openclaw/openclaw.json:
# {
#   "skills": {
#     "entries": {
#       "discord-voice": {
#         "env": {
#           "DISCORD_BOT_TOKEN": "YOUR_BOT_TOKEN"
#         }
#       }
#     }
#   }
# }

# Or pass token directly:
# python3 send_voice.py ... --token "YOUR_TOKEN"
