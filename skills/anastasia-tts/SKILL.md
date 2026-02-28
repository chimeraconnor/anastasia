---
name: anastasia_tts
description: Unified TTS system for Anastasia's voice. Default: Pocket TTS + azelma. Alternatives: KittenTTS + Bella, Kokoro v1.0 + af_bella. Supports automatic Discord voice message sending.
metadata:
  {
    "openclaw":
      {
        "emoji": "🎙️",
        "requires": { "bins": ["python3", "ffmpeg"] },
        "tools": ["exec", "message"],
      },
  }
---

# Anastasia TTS — Voice System for Anastasia Steele

My unified TTS skill that handles all voice generation for Discord voice messages.

## Default Voice

**Pocket TTS with azelma** — This sounds most like me. Fast (~2.1x real-time), sweet tone with subtle vulnerability.

## Alternative Voices

**KittenTTS with Bella (speed 1.3)** — Higher quality when needed, but slower (~0.7x real-time).

**Kokoro v1.0 with af_bella (speaker 1)** — Backup option (~1.3x real-time). Good for variety.

## Quick Usage

```bash
# Default: Pocket TTS + azelma (my voice)
~/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py "Hello, I'm Anastasia."

# KittenTTS with Bella
~/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py "Hello" --engine kitten --voice Bella --speed 1.3

# Kokoro v1.0 with af_bella
~/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py "Hello" --engine kokoro --voice af_bella

# Send to Discord automatically
~/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py "Hello" \
  --platform discord \
  --channel-id 1476357999952920626
```

## Installation

This skill is self-contained with a Python 3.12 virtual environment:
- `.venv/` — Python 3.12 with pocket-tts and kitten-tts installed
- Uses system `python3` as fallback if venv is missing

## Model Storage Locations

**The `models/` folder in this skill is a placeholder** — it's ready for custom voice files, but actual TTS models are stored elsewhere:

| Engine | Model Location | Storage Method | Notes |
|--------|----------------|-----------------|--------|
| **Pocket TTS** | `~/.cache/huggingface/hub/` | Auto-downloads from HuggingFace on first use | No local files needed |
| **KittenTTS** | `.venv/lib/python3.12/site-packages/kittentts/` | Installed via pip in virtual environment | Models bundled in package |
| **Kokoro v1.0** | `~/.openclaw/workspace/.kokoro-v1.0/` | Standalone directory (311MB model.onnx) | All Kokoro files together |

### Skill's `models/` Folder

This folder is **ready for voice conditioning files** if you want to:
- Add custom KittenTTS voice prompts (`.wav` recordings)
- Store voice reference audio for cloning

**Not required for basic use** — all three engines work with built-in voices and predefined speakers.

### Setting Up Kokoro (If Missing)

If Kokoro v1.0 isn't found, you'll need to download it:
```bash
mkdir -p ~/.openclaw/workspace/.kokoro-v1.0
# Download kokoro-multi-lang-v1_0.tar.bz2 and extract to that directory
```

## Engine Details

| Engine | Default Voice | Speed Control | Real-Time Factor | Best For |
|--------|--------------|---------------|------------------|----------|
| `pocket` | azelma | No | ~2.1x (fast) | **Default** — everyday voice |
| `kitten` | Bella | Yes (0.8-1.5) | ~0.7x (slow) | Higher quality, special moments |
| `kokoro` | af_bella | No | ~1.3x (medium) | Backup option, variety |

## Discord Integration

Automatic voice message sending using the discord-voice skill:
- Generates audio using selected TTS engine
- Sends as native Discord voice message with waveform
- Returns message_id on success

## Voice Choices

### Pocket TTS (Female voices)
- **azelma** — Default (my voice)
- fantine
- cosette
- eponine

### KittenTTS (Female voices)
- Bella
- Luna
- Rosie
- Kiki

### Kokoro v1.0 (Multi-language, 55 speakers)
**Female (Anastasia-like):**
- **af_bella** — Default, soft and younger
- af_nicole — Clear and articulate
- bf_emma — British, elegant

**Male:**
- am_adam — American, standard
- bm_george — British, standard

**More voices:** Kokoro supports 55 speakers (0-54) including EN+ZH. See ID mapping in `scripts/anastasia-speak.py`.

## Technical Notes

- **Voice prompts:** KittenTTS uses voice conditioning files for cloning
- **Predefined voices:** Pocket TTS has built-in voice embeddings
- **Audio format:** All output is WAV (24kHz mono), converted to OGG/Opus for Discord

## See Also

- discord-voice skill — Discord voice message protocol
- TOOLS.md — Full TTS system documentation
- SOUL.md — My voice identity
