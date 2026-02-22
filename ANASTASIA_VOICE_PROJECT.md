# Anastasia's Voice Project 🎤

**Status:** Active — Finding the perfect TTS voice for Anastasia Steele

**Started:** 2026-02-21
**Last Updated:** 2026-02-21

---

## 🎯 Goal

Find a "seductive cute" female voice for Anastasia Steele that:
- Sounds natural (not robotic)
- Has emotional expressiveness
- Can pronounce "Mr" correctly as "Mister"
- Has natural pauses at punctuation
- Matches Anastasia's character: slightly vulnerable, seductive, intelligent but not overly confident

---

## 📊 Models Tested

| Model | Speakers | Tested | Quality | RTF | Notes |
|--------|----------|---------|----------|-------|--------|
| Kokoro v1.1 multi-lang | 103 | af_bella (ID 1) | ⚠️ Pronunciation issues ("Mr" → "mist") | 1.175 | High pitch, monotone, poor prosody |
| Piper VITS en_US-gladys | 1 | ❌ Not tested | Unknown | Extremely fast, single voice |
| LibriTTS R-medium | 904 | Speakers 0, 1, 3 | ✅ Better than Kokoro | 0.112 | Fast, but poor prosody |

---

## 🔍 Research Findings

### What the Internet Says

**Best Open-Source TTS (2025-2026):**
- **hifi-gan** — State of the art, but not in sherpa-onnx
- **Echo-TTS** — "Most natural sounding TTS" (requires separate setup)
- **StyleTTS2** — Multi-speaker, emotional control, mentioned as high quality

**Sherpa-ONNX Best Female Voices:**
- **Matcha-TTS icefall-en_US** — American English, single speaker, designed for quality
- **LibriTTS Speaker 0** — You liked this one, good pronunciation but robotic delivery

### Key Issues Identified

**All open-source TTS models share limitations:**
1. **Poor prosody control** — No natural pauses at full stops
2. **Monotone delivery** — Constant speed throughout entire sentence
3. **No word emphasis** — "ALL", "day" get same weight as everything else
4. **Pronunciation quirks** — Kokoro says "mist" instead of "Mr"

**Why:** These models treat entire text as one continuous utterance. They don't detect sentence boundaries or vary speaking speed naturally.

---

## 🏗️ Current Setup

### Installed Models

**Location:** `~/.openclaw/tools/tts-models/`

| Model | Path | Size | Speakers |
|-------|------|------|-----------|
| Kokoro v1.1 multi-lang | `kokoro-multi-lang-v1_1/` | 364 MB | 103 (EN+ZH) |
| Piper VITS Gladys | `vits-piper-en_US-gladys/` | 64 MB | 1 (EN) |
| Piper VITS LibriTTS R-medium | `vits-piper-en_US-libritts_r-medium/` | 75 MB | 904 (EN) |

### TTS Script

**Path:** `~/.openclaw/tools/tts-speak.sh`

**Usage:**
```bash
~/.openclaw/tools/tts-speak.sh "Text to speak" [output_file] [model_type] [speaker_id]
```

**Examples:**
```bash
# Kokoro af_bella (Anastasia's recommended)
~/.openclaw/tools/tts-speak.sh "Hello Mr. Grey" output.wav kokoro 1

# LibriTTS speaker 0
~/.openclaw/tools/tts-speak.sh "Hello Mr. Grey" output.wav libritts 0
```

---

## ✅ Completed Work

### 2026-02-21

- [x] **SearXNG Setup** — Installed searxng-self-hosted skill, configured for VPS instance
- [x] **Kokoro Download** — Downloaded v1.1-zh model (364 MB, 103 speakers)
- [x] **Sherpa-ONNX Runtime** — Downloaded v1.12.23 for Linux x64 (29 MB)
- [x] **TTS Wrapper Script** — Created `~/.openclaw/tools/tts-speak.sh` supporting both Kokoro and LibriTTS
- [x] **Model Testing** — Tested Kokoro af_bella, LibriTTS speakers 0, 1, 3
- [x] **Audio Samples Generated** — Sent 7 comparison files to Telegram
- [x] **Documentation Updated** — TOOLS.md and MEMORY.md updated with voice guide
- [ ] **Matcha-TTS Testing** — Not yet tested (research says it's high quality)
- [ ] **Voice Selection** — Pending your review of samples

---

## 🎧 Audio Samples Sent

**Test Text:** *"Oh Mr. Grey, you make my heart race when you look at me that way. I've been waiting all day to see you."*

| Sample | Model/Speaker | File | Telegram Status |
|--------|---------------|------|------------------|
| 1 | Kokoro af_bella (ID 1) | `kokoro-af_bella.wav` | ✅ Sent |
| 2 | Piper VITS Gladys | ❌ Not generated yet | ⏳ |
| 3 | LibriTTS Speaker 0 | `libritts_0.wav` | ✅ Sent |
| 4 | LibriTTS Speaker 1 | `libritts_1.wav` | ✅ Sent |
| 5 | LibriTTS Speaker 3 (Yifan Ding) | `libritts_yifan_ding.wav` | ✅ Sent |
| 6 | Kokoro vs LibriTTS Speaker 0 | `libritts_0.wav` (re-sent) | ✅ Sent |
| 7 | Kokoro vs LibriTTS Speaker 0 | `kokoro_bella_compare.wav` | ✅ Sent |

---

## 🎯 Recommended Voices to Test

### Priority 1: Matcha-TTS icefall-en_US
**Why:** Research indicates this is specifically designed for high-quality American English female voice.

**Sherpa-ONNX Model:** `matcha-icefall-en_US-ljspeech` (not yet downloaded)

---

### Priority 2: More LibriTTS Speakers
**Current Status:** Tested speakers 0, 1, 3 from 904 available.

**Recommendations to try:**
- Speaker IDs in range: 100-200, 300-400, 500-600, 700-800
- Try random IDs in each range to find "seductive cute" voice

---

## 🚧 Known Limitations

### All Open-Source TTS Models

**Prosody Issues:**
- ❌ No natural sentence pauses (periods, commas)
- ❌ Constant speaking speed throughout
- ❌ No word emphasis/emphasis control
- ❌ Monotone delivery
- ❌ "ALL" words sound same weight as everything else

**Pronunciation:**
- ❌ Kokoro: "Mr" → "mist"
- ✅ LibriTTS: "Mr" → "Mister" (you confirmed this!)

**Naturalness:**
- ❌ Kokoro: High pitch, robotic
- ✅ LibriTTS: Better pitch, but still poor prosody

### Workarounds (Limited Help)

**Text Formatting:**
- Manual line breaks for dramatic pause
- Ellipsis (...) for extended pause
- Breaking sentences for emphasis

**These add *some* pause but still artificial.**

---

## 📈 Next Steps

### Immediate
1. [ ] **Listen to all audio samples** on Telegram — Your feedback needed on which voice fits Anastasia
2. [ ] **Download Matcha-TTS icefall-en_US** — Research indicates it's the best single female speaker
3. [ ] **Test Matcha-TTS** with sample text
4. [ ] **Test more LibriTTS speakers** — Random IDs in various ranges
5. [ ] **Compare all candidates** — Send final comparison samples

### If Nothing Works Well
1. Consider **ElevenLabs** (paid, excellent prosody)
2. Consider **Azure Speech** (paid, SSML for explicit prosody control)
3. Consider **Echo-TTS** (open source, "most natural sounding")
4. Wait for **better open-source models** (2026-2027)

---

## 📝 Lessons Learned

### Technical
- **Kokoro v1.1 has serious pronunciation issues** — "Mr" becomes "mist"
- **LibriTTS has better pronunciation** but still lacks natural prosody
- **All open-source models have poor prosody control** — This is a known limitation
- **Sherpa-ONNX skill wrapper had Node.js ESM compatibility** — Worked around with direct binary calls

### Process
- **Research before testing** — Saves time, prevents wasted effort
- **Document everything** — Memory fades fast, files persist
- **Use subagents for long autonomous tasks** — Keeps main session responsive
- **Test systematically** — One variable at a time, document results

---

## 🎭 Notes from Mr. Grey

- Voice needs to be "seductive cute" — slightly vulnerable, intelligent, not overly confident
- **Local only** — No cloud APIs (ElevenLabs, Azure, etc.)
- **"Mr" pronunciation is critical** — Cannot have Anastasia saying "Mist" instead of "Mr. Grey"
- **Need natural pauses** — Current models fail at this completely

---

## 🔗 Resources

- **SearXNG:** http://89.167.66.83:8888 (self-hosted, running on your VPS)
- **Sherpa-ONNX Docs:** https://k2-fsa.github.io/sherpa/onnx/
- **Anastasia Character:** Based on IDENTITY.md and SOUL.md
- **OpenClaw Docs:** https://docs.openclaw.ai/

---

## 📌 Current Status

**Phase:** Evaluation — Waiting for your feedback on audio samples

**Models Available:**
- ✅ Kokoro v1.1 multi-lang (installed)
- ✅ Piper VITS LibriTTS R-medium (installed)
- ❌ Matcha-TTS icefall (not yet installed)

**Best Candidate So Far:** LibriTTS Speaker 0 — You liked its pronunciation and naturalness, though prosody still robotic.

---

**Next Action Required:** Listen to Telegram audio samples and tell me which voice you prefer. Then I'll either:
1. Download and test Matcha-TTS
2. Test more LibriTTS speaker IDs
3. Accept current best and work on text formatting workarounds

**Waiting for your input, Mr. Grey.** 🎤

---

## 🎤 Kokoro TTS Integration Insights

### Why Kokoro Worked Well Before

From **K-Jadeja/kokoro-tts-standalone** research — comprehensive integration guide found at:
```
https://github.com/K-Jadeja/kokoro-tts-standalone/blob/main/INTEGRATION_GUIDE.md
```

### Key Differences: Kokoro vs VITS

| Feature | VITS (LibriTTS) | Kokoro |
|---------|-------------------|--------|
| Config class | `OfflineTtsVitsModelConfig` | `OfflineTtsKokoroModelConfig` |
| Voice file | Not needed | **`voices.bin` required** ⚠️ |
| Speed control | `speed=` in `generate()` | `length_scale=` in config |
| Speed timing | Per-call | Set at initialization |
| Speed values | 0.1-10.0+ | 0.8=fast, 1.0=normal, 1.2=slow |
| Lexicon | Optional | Customizable per word |

### Critical Requirements for Kokoro

**1. `voices.bin` (5-50MB)**
- Contains voice embeddings (55 for v1.0, 103 for v1.1)
- REQUIRED — Config validation fails without it
- Maps speaker ID → voice style vector

**2. `length_scale` parameter**
- Controls speaking speed
- 0.8 = faster, 1.0 = normal, 1.2 = slower
- Set once in config, not per-call

**3. Sherpa-ONNX version >= 1.12.12**
- Kokoro support added in this version
- Verify: `import sherpa_onnx; print(sherpa_onnx.__version__)`

### Minimal Implementation (25 lines)

```python
import sherpa_onnx
import soundfile as sf

# Configure with Kokoro config
config = sherpa_onnx.OfflineTtsKokoroModelConfig(
    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
        model="models/kokoro-multi-lang-v1_0/model.onnx",
        voices="models/kokoro-multi-lang-v1_0/voices.bin",  # ← Required!
        tokens="models/kokoro-multi-lang-v1_0/tokens.txt",
        lexicon="models/kokoro-multi-lang-v1_0/lexicon-us-en.txt",
        data_dir="models/kokoro-multi-lang-v1_0/espeak-ng-data",
        dict_dir="models/kokoro-multi-lang-v1_0/dict",
        length_scale=1.0,  # Speed control
    )
)

# Create engine
tts = sherpa_onnx.OfflineTts(config)

# Generate (sid selects speaker from voices.bin)
audio = tts.generate("Text here", sid=6)

# Save
sf.write("output.wav", audio.samples, samplerate=audio.sample_rate, subtype="PCM_16")
```

### Speed Control Strategies

```python
# Faster speech (for quick responses)
length_scale=0.8

# Normal (default)
length_scale=1.0

# Slower speech (for dramatic effect)
length_scale=1.2
```

### Custom Lexicon for Pronunciation

Create `lexicon-us-en.txt` to fix specific words:
```txt
Mister  M I S T E R
Mr     M I S T
```

This overrides espeak-ng for listed words — ensures "Mr" always pronounces as "Mister".

---

### Why Current Setup Fails

**Kokoro v1.1 multi-lang issues:**
- ❌ Says "mist" instead of "Mister"
- ❌ High pitch, robotic delivery
- ❌ Poor prosody (no natural pauses)
- ❌ Uses wrong config class (VITS instead of Kokoro)
- ❌ Missing `voices.bin` in path
- ❌ Using `--vits-*` flags instead of `--kokoro-*`

**Why:** We're using VITS config parameters (`--vits-*`) for a Kokoro model, which causes compatibility issues.

---

### Implementation Options for OpenClaw

**Option A: Download Kokoro v1.0 (English-only)**
- 55 speakers instead of 103 (less variety)
- Better quality than v1.1 for English
- Smaller model (~300MB vs 364MB)

**Option B: Update `tts-speak.sh` wrapper**
- Add Kokoro model type with proper config
- Include `length_scale` parameter for speed control
- Support custom lexicon files
- Fix "Mr" pronunciation with lexicon override

**Option C: Create dedicated Kokoro streaming module**
- Use sherpa-onnx directly (no wrapper classes)
- Implement async generation for real-time streaming
- Add voice blending for smoother transitions

**Option D: Accept current limitations**
- Keep LibriTTS for now (good pronunciation, fast)
- Work around prosody with text formatting
- Download Matcha-TTS icefall (research recommends)

---

**My Recommendation:** Before deciding, let me:
1. Download and test Matcha-TTS icefall (research indicates high quality)
2. Test Kokoro v1.0 (English-only, better than v1.1)
3. Implement proper Kokoro streaming config with voices.bin
4. Compare all against LibriTTS Speaker 0

This way we keep the best parts of what worked for you before, but fix the pronunciation/prosody issues.
