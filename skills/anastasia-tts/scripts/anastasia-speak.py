#!/usr/bin/env python3
"""
Anastasia's Unified TTS Wrapper
Supports Pocket TTS (default) and KittenTTS with Discord auto-sending
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Skill paths
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
TEMP_OUTPUT = Path("/tmp/anastasia-tts-output.wav")

# Voice configurations
VOICES = {
    "pocket": {
        "default": "azelma",
        "voices": ["azelma", "fantine", "cosette", "eponine"],
        "env_python": SKILL_DIR / ".venv" / "bin" / "python3",
        "env_name": "pocket-tts",
    },
    "kitten": {
        "default": "Bella",
        "voices": ["Bella", "Luna", "Rosie", "Kiki"],
        "env_python": SKILL_DIR / ".venv" / "bin" / "python3",
        "env_name": "kitten-tts",
    },
    "kokoro": {
        "default": "af_bella",
        "voices": ["af_bella", "af_nicole", "am_adam", "bf_emma", "bm_george"],
        "speaker_ids": {
            "af_bella": 1,
            "af_nicole": 6,
            "am_adam": 10,
            "bf_emma": 20,
            "bm_george": 30,
        },
        "env_name": "kokoro-v1.0",
    },
}


def get_pocket_tts(text: str, output: Path, voice: str = "azelma") -> subprocess.CompletedProcess:
    """Generate speech using Pocket TTS (azelma by default)"""
    # Pocket TTS uses predefined voice names, not file paths
    cmd = [
        VOICES["pocket"]["env_python"],
        "-m",
        "pocket_tts",
        "generate",
        "--text", text,
        "--voice", voice,
        "--output-path", str(output),
        "--device", "cpu",
    ]

    return subprocess.run(cmd, capture_output=True, text=True)


def get_kitten_tts(text: str, output: Path, voice: str = "Bella", speed: float = 1.3) -> subprocess.CompletedProcess:
    """Generate speech using KittenTTS mini-0.8"""
    # KittenTTS voice conditioning file path (would need to be set up)
    voice_prompt = str(SKILL_DIR / "models" / f"{voice}.wav")

    cmd = [
        VOICES["kitten"]["env_python"],
        str(SCRIPTS_DIR / "kitten-speak.py" if (SCRIPTS_DIR / "kitten-speak.py").exists() else Path.home() / ".openclaw" / "workspace" / "tools" / "tts" / "kitten" / "kitten-speak.py"),
        text,
        str(output),
        voice,
        str(speed),
    ]

    # Check if kitten-speak.py exists in workspace
    if not Path(cmd[2]).exists():
        print(f"Warning: kitten-speak.py not found at {cmd[2]}")
        return subprocess.CompletedProcess(cmd[2], 1, "", "kitten-speak.py not found")

    return subprocess.run(cmd, capture_output=True, text=True)


def get_kokoro_tts(text: str, output: Path, voice: str = "af_bella") -> subprocess.CompletedProcess:
    """Generate speech using Sherpa-ONNX Kokoro v1.0"""
    kokoro_dir = Path.home() / ".openclaw" / "workspace" / ".kokoro-v1.0"
    sherpa_dir = Path.home() / ".openclaw" / "workspace" / "tools" / "sherpa-onnx-tts" / "runtime"

    # Get speaker ID from voice name
    speaker_id = VOICES["kokoro"]["speaker_ids"].get(voice, 1)

    # Set up library path
    env = dict(
        LD_LIBRARY_PATH=f"{sherpa_dir / 'lib'}:{os.environ.get('LD_LIBRARY_PATH', '')}",
    )

    cmd = [
        str(sherpa_dir / "bin" / "sherpa-onnx-offline-tts"),
        f"--kokoro-model={kokoro_dir / 'model.onnx'}",
        f"--kokoro-voices={kokoro_dir / 'voices.bin'}",
        f"--kokoro-tokens={kokoro_dir / 'tokens.txt'}",
        f"--kokoro-data-dir={kokoro_dir / 'espeak-ng-data'}",
        f"--kokoro-lexicon={kokoro_dir / 'lexicon-us-en.txt'}",
        f"--sid={speaker_id}",
        f"--output-filename={output}",
        text,
    ]

    return subprocess.run(cmd, env=env, capture_output=True, text=True)


def send_to_discord(audio_file: Path, channel_id: str) -> subprocess.CompletedProcess:
    """Send audio as Discord voice message"""
    send_voice_script = Path.home() / ".openclaw" / "workspace" / "skills" / "discord-voice" / "scripts" / "send_voice.py"

    cmd = [
        "python3",
        str(send_voice_script),
        "--channel-id", channel_id,
        "--audio-file", str(audio_file),
    ]

    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description="Anastasia's TTS - Generate voice messages")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("--engine", choices=["pocket", "kitten", "kokoro"], default="pocket", help="TTS engine (default: pocket)")
    parser.add_argument("--voice", help="Voice name (default: engine default)")
    parser.add_argument("--speed", type=float, default=1.3, help="Speed for kitten engine (default: 1.3)")
    parser.add_argument("--platform", choices=["discord", "none"], default="none", help="Where to send (default: none)")
    parser.add_argument("--channel-id", help="Discord channel ID for voice message")

    args = parser.parse_args()

    # Select voice
    voice = args.voice or VOICES[args.engine]["default"]

    # Validate voice exists
    if voice not in VOICES[args.engine]["voices"]:
        print(f"Error: Voice '{voice}' not found for {args.engine}")
        print(f"Available voices for {args.engine}: {', '.join(VOICES[args.engine]['voices'])}")
        sys.exit(1)

    # Generate audio
    print(f"Generating {args.engine} TTS with voice '{voice}'...")

    if args.engine == "pocket":
        result = get_pocket_tts(args.text, TEMP_OUTPUT, voice)
    elif args.engine == "kitten":
        result = get_kitten_tts(args.text, TEMP_OUTPUT, voice, args.speed)
    else:  # kokoro
        result = get_kokoro_tts(args.text, TEMP_OUTPUT, voice)

    if result.returncode != 0:
        print(f"TTS generation failed: {result.stderr}")
        sys.exit(1)

    print(f"Audio generated: {TEMP_OUTPUT}")

    # Send to Discord if requested
    if args.platform == "discord":
        if not args.channel_id:
            print("Error: --channel-id required for Discord sending")
            sys.exit(1)

        print(f"Sending to Discord channel {args.channel_id}...")
        result = send_to_discord(TEMP_OUTPUT, args.channel_id)

        if result.returncode != 0:
            print(f"Discord send failed: {result.stderr}")
            sys.exit(1)

        print("Voice message sent successfully!")


if __name__ == "__main__":
    main()
