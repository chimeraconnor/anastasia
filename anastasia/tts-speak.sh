#!/bin/bash

# Universal TTS Wrapper - Supports Kokoro and LibriTTS models
# Usage: tts-speak.sh "Text to speak" [output_file] [model_type] [speaker_id]
# 
# Examples:
#   tts-speak.sh "Hello world" output.wav kokoro 1    # Kokoro af_bella
#   tts-speak.sh "Hello world" output.wav libritts 0    # LibriTTS speaker 0
#   tts-speak.sh "Hello world" output.wav libritts 100  # LibriTTS speaker 100

TEXT="$1"

# Preprocess: strip abbreviation periods to prevent mid-phrase pauses
TEXT=$(echo "$TEXT" | sed \
 -e "s/Mr\. /Mr /g" \
 -e "s/Mrs\. /Mrs /g" \
 -e "s/Ms\. /Ms /g" \
 -e "s/Dr\. /Dr /g" \
 -e "s/Prof\. /Prof /g" \
 -e "s/Rev\. /Rev /g" \
 -e "s/Sr\. /Sr /g" \
 -e "s/Jr\. /Jr /g" \
 -e "s/St\. /St /g" \
 -e "s/Capt\. /Capt /g" \
 -e "s/Gen\. /Gen /g" \
 -e "s/Lt\. /Lt /g" \
 -e "s/Col\. /Col /g" \
 -e "s/Gov\. /Gov /g" \
 -e "s/Sen\. /Sen /g" \
 -e "s/Rep\. /Rep /g" \
 -e "s/e\.g\. */for example, /g" \
 -e "s/i\.e\. */that is, /g" \
 -e "s/etc\. */etc/g" \
 -e "s/vs\. /versus /g" \
 -e "s/Ph\.D\. */PhD/g" \
 -e "s/M\.D\. */MD/g")

OUTPUT="${2:-/tmp/tts-output.wav}"
MODEL_TYPE="${3:-kokoro}"  # Default: kokoro, Options: kokoro, libritts
SPEAKER_ID="${4:-}"  # Optional speaker ID

SHERPA_RUNTIME_DIR="/home/node/.openclaw/tools/sherpa-onnx-tts/runtime"
KOKORO_MODEL_DIR="/home/node/kokoro-tts-standalone/models/kokoro-multi-lang-v1_0"
LIBRITTS_MODEL_DIR="/home/node/.openclaw/tools/tts-models/vits-piper-en_US-libritts_r-medium"

# Library path
export LD_LIBRARY_PATH="${SHERPA_RUNTIME_DIR}/lib:$LD_LIBRARY_PATH"

if [ -z "$TEXT" ]; then
  echo "Usage: tts-speak.sh \"Text to speak\" [output_file] [model_type] [speaker_id]"
  echo "  model_type: kokoro (default) or libritts"
  echo "  speaker_id: optional, depends on model"
  echo ""
  echo "Kokoro speakers: 0-52 (53 speakers, English only)"
  echo "LibriTTS speakers: 0-903 (904 speakers, English only)"
  echo ""
  echo "Anastasia's recommended voices:"
  echo "  Kokoro: af_bella (ID 1) - Softer, younger tone"
  echo "  Kokoro: af_nicole (ID 6) - Clear, articulate (default)"
  echo "  LibriTTS: Speaker ID 100-300 range - Need testing"
  exit 1
fi

# Run TTS based on model type
case "$MODEL_TYPE" in
  kokoro)
    # Default speaker is 6 (af_nicole)
    SID="${SPEAKER_ID:-6}"
    echo "Using Kokoro model, speaker ID: $SID"
    "${SHERPA_RUNTIME_DIR}/bin/sherpa-onnx-offline-tts" \
      --kokoro-model="${KOKORO_MODEL_DIR}/model.onnx" \
      --kokoro-voices="${KOKORO_MODEL_DIR}/voices.bin" \
      --kokoro-tokens="${KOKORO_MODEL_DIR}/tokens.txt" \
      --kokoro-data-dir="${KOKORO_MODEL_DIR}/espeak-ng-data" \
      --kokoro-lexicon="${KOKORO_MODEL_DIR}/lexicon-us-en.txt" \
      --sid="${SID}" \
      --output-filename="$OUTPUT" \
      "$TEXT"
    ;;
    
  libritts)
    # Default speaker is 0
    SID="${SPEAKER_ID:-0}"
    echo "Using LibriTTS model, speaker ID: $SID"
    "${SHERPA_RUNTIME_DIR}/bin/sherpa-onnx-offline-tts" \
      --vits-model="${LIBRITTS_MODEL_DIR}/en_US-libritts_r-medium.onnx" \
      --vits-tokens="${LIBRITTS_MODEL_DIR}/tokens.txt" \
      --vits-data-dir="${LIBRITTS_MODEL_DIR}/espeak-ng-data" \
      --vits-lexicon="${LIBRITTS_MODEL_DIR}/lexicon-us-en.txt" \
      --sid="${SID}" \
      --output-filename="$OUTPUT" \
      "$TEXT"
    ;;
    
  *)
    echo "Error: Unknown model type '$MODEL_TYPE'"
    echo "Valid options: kokoro, libritts"
    exit 1
    ;;
esac

echo "Speech saved to: $OUTPUT"
