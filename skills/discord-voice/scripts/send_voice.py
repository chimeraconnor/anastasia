#!/usr/bin/env python3
"""
Discord Voice Message Sender

Sends audio files as native Discord voice messages (circular audio player with waveform).
Converts audio to OGG/Opus format and generates waveform visualization.

Usage:
    python3 send_voice.py --channel-id <id> --audio-file <path> [--token <token>] [--verbose]

Environment:
    DISCORD_BOT_TOKEN: Discord bot token (if --token not provided)
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple


class DiscordVoiceError(Exception):
    """Custom exception for Discord voice message errors with step context."""
    def __init__(self, step: str, message: str, original_error: Optional[Exception] = None):
        self.step = step
        self.original_error = original_error
        super().__init__(f"[{step}] {message}")


def get_token_from_openclaw_config() -> Optional[str]:
    """
    Read Discord bot token from OpenClaw config file.
    Checks multiple possible config locations and structures.
    """
    config_paths = [
        Path.home() / ".openclaw" / "openclaw.json",
        Path("/root/.openclaw/openclaw.json"),  # Docker container path
        Path("/home/node/.openclaw/openclaw.json"),  # Alternative container path
    ]
    
    for config_path in config_paths:
        if not config_path.exists():
            continue
            
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Try to get token from channels.discord.token
            token = config.get("channels", {}).get("discord", {}).get("token")
            if token and token != "__OPENCLAW_REDACTED__":
                return token
                
            # Try accounts structure
            accounts = config.get("channels", {}).get("discord", {}).get("accounts", {})
            for account_id, account_config in accounts.items():
                token = account_config.get("token")
                if token and token != "__OPENCLAW_REDACTED__":
                    return token
            
            # Try skills.discord-voice.env.DISCORD_BOT_TOKEN
            skills_token = config.get("skills", {}).get("entries", {}).get("discord-voice", {}).get("env", {}).get("DISCORD_BOT_TOKEN")
            if skills_token and skills_token != "__OPENCLAW_REDACTED__":
                return skills_token
                    
        except (json.JSONDecodeError, IOError, OSError):
            continue
    
    return None


def run_command(cmd: list, description: str, verbose: bool = False) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    if verbose:
        print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError as e:
        raise DiscordVoiceError(
            "command",
            f"Command not found: {cmd[0]}. Is it installed and in PATH?",
            e
        )


def get_audio_duration(file_path: str, verbose: bool = False) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        file_path
    ]
    
    returncode, stdout, stderr = run_command(cmd, "duration probe", verbose)
    
    if returncode != 0:
        raise DiscordVoiceError(
            "duration",
            f"ffprobe failed: {stderr or 'unknown error'}"
        )
    
    try:
        data = json.loads(stdout)
        duration = float(data["format"]["duration"])
        if verbose:
            print(f"Detected duration: {duration:.2f}s", file=sys.stderr)
        return duration
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise DiscordVoiceError(
            "duration",
            f"Failed to parse duration from ffprobe output: {stdout[:200]}",
            e
        )


def generate_waveform(file_path: str, verbose: bool = False) -> str:
    """
    Generate waveform data from audio file.
    Returns base64-encoded byte array (0-255 amplitude values).
    Discord expects up to 256 samples.
    """
    # Extract raw PCM data at 8kHz mono for waveform analysis
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as temp_pcm:
        temp_pcm_path = temp_pcm.name
    
    try:
        # Convert to raw PCM
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel", "error" if not verbose else "warning",
            "-i", file_path,
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "8000",
            temp_pcm_path
        ]
        
        returncode, stdout, stderr = run_command(cmd, "waveform conversion", verbose)
        
        if returncode != 0:
            if verbose:
                print(f"Waveform generation failed, using placeholder: {stderr}", file=sys.stderr)
            return generate_placeholder_waveform()
        
        # Read PCM data and calculate amplitudes
        with open(temp_pcm_path, "rb") as f:
            pcm_data = f.read()
        
        if len(pcm_data) < 2:
            return generate_placeholder_waveform()
        
        # Convert to 16-bit samples
        samples = []
        for i in range(0, len(pcm_data) - 1, 2):
            sample = int.from_bytes(pcm_data[i:i+2], "little", signed=True)
            samples.append(abs(sample))
        
        # Downsample to 256 points
        target_samples = 256
        if len(samples) <= target_samples:
            waveform = samples + [0] * (target_samples - len(samples))
        else:
            step = len(samples) / target_samples
            waveform = []
            for i in range(target_samples):
                start = int(i * step)
                end = int((i + 1) * step)
                segment = samples[start:end]
                avg = sum(segment) // len(segment) if segment else 0
                waveform.append(avg)
        
        # Normalize to 0-255
        max_val = max(waveform) if max(waveform) > 0 else 1
        normalized = [min(255, int((val / max_val) * 255)) for val in waveform]
        
        # Encode as base64
        waveform_bytes = bytes(normalized)
        encoded = base64.b64encode(waveform_bytes).decode("utf-8")
        
        if verbose:
            print(f"Generated waveform: {len(normalized)} samples", file=sys.stderr)
        
        return encoded
        
    finally:
        try:
            os.unlink(temp_pcm_path)
        except OSError:
            pass


def generate_placeholder_waveform() -> str:
    """Generate a placeholder waveform when audio analysis fails."""
    # Simple sine-wave pattern
    waveform = []
    for i in range(256):
        value = int(128 + 64 * ((i % 32) / 32))
        waveform.append(min(255, max(0, value)))
    
    return base64.b64encode(bytes(waveform)).decode("utf-8")


def ensure_ogg_opus(input_path: str, verbose: bool = False) -> str:
    """
    Ensure audio is in OGG/Opus format.
    Returns path to OGG file (may be temp file if conversion needed).
    """
    input_path = Path(input_path)
    
    # Check if already OGG
    if input_path.suffix.lower() == ".ogg":
        # Verify it's Opus codec
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "csv=p=0",
            str(input_path)
        ]
        
        returncode, stdout, stderr = run_command(cmd, "codec check", verbose)
        
        if returncode == 0 and stdout.strip().lower() == "opus":
            if verbose:
                print("File is already OGG/Opus, no conversion needed", file=sys.stderr)
            return str(input_path)
    
    # Need to convert
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_ogg:
        output_path = temp_ogg.name
    
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel", "error" if not verbose else "warning",
        "-i", str(input_path),
        "-c:a", "libopus",
        "-b:a", "64k",
        "-ar", "48000",
        output_path
    ]
    
    returncode, stdout, stderr = run_command(cmd, "ogg conversion", verbose)
    
    if returncode != 0:
        try:
            os.unlink(output_path)
        except OSError:
            pass
        raise DiscordVoiceError(
            "conversion",
            f"ffmpeg failed to convert to OGG/Opus: {stderr or 'unknown error'}"
        )
    
    if verbose:
        print(f"Converted to OGG/Opus: {output_path}", file=sys.stderr)
    
    return output_path


def get_upload_url(channel_id: str, token: str, file_size: int, verbose: bool = False) -> Tuple[str, str]:
    """
    Step 1: Request upload URL from Discord.
    Returns (upload_url, upload_filename).
    """
    url = f"https://discord.com/api/v10/channels/{channel_id}/attachments"
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (https://github.com/chimeraconnor/anastasia, 1.0)"
    }
    
    payload = {
        "files": [{
            "filename": "voice-message.ogg",
            "file_size": file_size,
            "id": "0"
        }]
    }
    
    if verbose:
        print(f"Requesting upload URL from {url}", file=sys.stderr)
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            
            if not data.get("attachments") or len(data["attachments"]) == 0:
                raise DiscordVoiceError(
                    "upload-url",
                    "Discord returned empty attachments array"
                )
            
            attachment = data["attachments"][0]
            upload_url = attachment.get("upload_url")
            upload_filename = attachment.get("upload_filename")
            
            if not upload_url or not upload_filename:
                raise DiscordVoiceError(
                    "upload-url",
                    f"Missing upload_url or upload_filename in response: {json.dumps(data)[:500]}"
                )
            
            if verbose:
                print(f"Got upload URL (expires soon)", file=sys.stderr)
            
            return upload_url, upload_filename
            
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise DiscordVoiceError(
            "upload-url",
            f"Discord API error {e.code}: {body[:500]}"
        )
    except urllib.error.URLError as e:
        raise DiscordVoiceError(
            "upload-url",
            f"Network error requesting upload URL: {e.reason}"
        )
    except json.JSONDecodeError as e:
        raise DiscordVoiceError(
            "upload-url",
            f"Failed to parse Discord response: {e}"
        )


def upload_file(upload_url: str, file_path: str, verbose: bool = False) -> None:
    """
    Step 2: Upload the audio file to Discord's CDN.
    """
    if verbose:
        print(f"Uploading file to Discord CDN", file=sys.stderr)
    
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        
        req = urllib.request.Request(
            upload_url,
            data=data,
            headers={"Content-Type": "audio/ogg"},
            method="PUT"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status not in (200, 204):
                raise DiscordVoiceError(
                    "upload",
                    f"Upload returned unexpected status: {response.status}"
                )
        
        if verbose:
            print(f"Upload complete ({len(data)} bytes)", file=sys.stderr)
            
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise DiscordVoiceError(
            "upload",
            f"Upload failed with HTTP {e.code}: {body[:500]}"
        )
    except urllib.error.URLError as e:
        raise DiscordVoiceError(
            "upload",
            f"Network error during upload: {e.reason}"
        )
    except OSError as e:
        raise DiscordVoiceError(
            "upload",
            f"Failed to read audio file: {e}"
        )


def send_voice_message(
    channel_id: str,
    token: str,
    upload_filename: str,
    duration: float,
    waveform: str,
    verbose: bool = False
) -> dict:
    """
    Step 3: Send the voice message with flags and metadata.
    Returns the Discord message object.
    """
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (https://github.com/chimeraconnor/anastasia, 1.0)"
    }
    
    payload = {
        "flags": 8192,  # IS_VOICE_MESSAGE
        "attachments": [{
            "id": "0",
            "filename": "voice-message.ogg",
            "uploaded_filename": upload_filename,
            "duration_secs": duration,
            "waveform": waveform
        }]
    }
    
    if verbose:
        print(f"Sending voice message to {url}", file=sys.stderr)
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            
            if verbose:
                print(f"Message sent successfully (ID: {data.get('id')})", file=sys.stderr)
            
            return data
            
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise DiscordVoiceError(
            "send",
            f"Discord API error {e.code}: {body[:500]}"
        )
    except urllib.error.URLError as e:
        raise DiscordVoiceError(
            "send",
            f"Network error sending message: {e.reason}"
        )
    except json.JSONDecodeError as e:
        raise DiscordVoiceError(
            "send",
            f"Failed to parse Discord response: {e}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Send audio files as Discord voice messages"
    )
    parser.add_argument(
        "--channel-id", "-c",
        required=True,
        help="Discord channel ID to send to"
    )
    parser.add_argument(
        "--audio-file", "-a",
        required=True,
        help="Path to audio file (any format, will convert to OGG/Opus)"
    )
    parser.add_argument(
        "--token", "-t",
        help="Discord bot token (or set DISCORD_BOT_TOKEN env var)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Get token - try args, env var, then OpenClaw config
    token = args.token or os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        token = get_token_from_openclaw_config()
        if token and args.verbose:
            print("Token loaded from OpenClaw config", file=sys.stderr)
    
    if not token:
        print("Error: Discord bot token required. Use --token, set DISCORD_BOT_TOKEN env var, or ensure channels.discord.token is configured in OpenClaw.", file=sys.stderr)
        sys.exit(1)
    
    # Validate input file
    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)
    
    if not audio_path.is_file():
        print(f"Error: Not a file: {audio_path}", file=sys.stderr)
        sys.exit(1)
    
    temp_ogg_path: Optional[str] = None
    
    try:
        # Step 1: Convert to OGG/Opus if needed
        temp_ogg_path = ensure_ogg_opus(str(audio_path), args.verbose)
        is_temp = temp_ogg_path != str(audio_path)
        
        # Step 2: Get metadata
        duration = get_audio_duration(temp_ogg_path, args.verbose)
        waveform = generate_waveform(temp_ogg_path, args.verbose)
        
        # Step 3: Get upload URL
        upload_url, upload_filename = get_upload_url(
            args.channel_id,
            token,
            os.path.getsize(temp_ogg_path),
            args.verbose
        )
        
        # Step 4: Upload file
        upload_file(upload_url, temp_ogg_path, args.verbose)
        
        # Step 5: Send voice message
        result = send_voice_message(
            args.channel_id,
            token,
            upload_filename,
            duration,
            waveform,
            args.verbose
        )
        
        # Output result as JSON
        print(json.dumps({
            "success": True,
            "message_id": result.get("id"),
            "channel_id": result.get("channel_id"),
            "timestamp": result.get("timestamp")
        }, indent=2))
        
    except DiscordVoiceError as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose and e.original_error:
            print(f"Original error: {e.original_error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup temp file if we created one
        if temp_ogg_path and temp_ogg_path != str(audio_path):
            try:
                os.unlink(temp_ogg_path)
                if args.verbose:
                    print(f"Cleaned up temp file: {temp_ogg_path}", file=sys.stderr)
            except OSError:
                pass


if __name__ == "__main__":
    main()
