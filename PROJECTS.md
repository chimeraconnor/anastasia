# OpenClaw Discord Feature Implementation Plan

**Created:** 2026-02-23
**Purpose:** Track Discord/OpenClaw feature implementations and planned additions

---

## ✅ ALREADY IMPLEMENTED

| Feature | Status | Reference |
|---------|--------|-----------|
| Basic Discord bot setup | ✅ | [Discord Setup](https://docs.openclaw.ai/channels/discord) |
| Guild allowlist | ✅ | [Access Control](https://docs.openclaw.ai/channels/discord#access-control-and-routing) |
| Model switching (`/model`) | ✅ | [Slash Commands](https://docs.openclaw.ai/tools/slash-commands) |
| Native slash commands | ✅ | [Slash Commands](https://docs.openclaw.ai/tools/slash-commands) |
| Model aliases (kimi, glm, flashx, GLM) | ✅ | `agents.defaults.models` config |
| **Live Stream Preview** (streaming) | ✅ 2026-02-23 | `channels.discord.streaming: "partial"` |
| **Ack Reaction** (👀) | ✅ 2026-02-23 | `channels.discord.ackReaction: "👀"` |
| **Bot Presence/Status** (dynamic rotation) | ✅ 2026-02-23 | Cron job + `message set-presence` |

**Current Aliases:**
- `kimi` → kimi-coding/k2p5
- `glm` → zai/glm-4.7
- `flashx` → zai/glm-4-flash
- `flashx47` → zai/glm-4.7-flashx
- `GLM` → zai/glm-5

---

## 🔧 IMMEDIATE ADDITIONS (Quick Wins)

| Priority | Feature | What It Does | Config/Command | Reference |
|----------|---------|--------------|----------------|-----------|
| ~~1~~ ✅ | ~~Live Stream Preview~~ | ~~Shows typing indicator while generating responses~~ | ~~`channels.discord.streaming: "partial"`~~ | [Streaming](https://docs.openclaw.ai/channels/discord#live-stream-preview) |
| ~~1~~ ✅ | ~~Ack Reaction~~ | ~~👀 emoji while processing~~ | ~~`channels.discord.ackReaction: "👀"`~~ | [Ack Reactions](https://docs.openclaw.ai/channels/discord#ack-reactions) |
| ~~1~~ ✅ | ~~Bot Presence/Status~~ | ~~Shows "Playing..." or custom status~~ | ~~`channels.discord.activity: "Helping Mr. Grey"`~~ | [Presence](https://docs.openclaw.ai/channels/discord#presence-configuration) |
| 3 | **Reply Tags** | Native Discord reply threading | `channels.discord.replyToMode: "first"` | [Reply Tags](https://docs.openclaw.ai/channels/discord#reply-tags-and-native-replies) |
| 4 | **Reaction Notifications** | Get notified when users react | `channels.discord.reactions: "own"` | [Reactions](https://docs.openclaw.ai/channels/discord#reaction-notifications) |

---

## 🎮 INTERACTIVE FEATURES (Medium Effort)

| Feature | What It Does | Implementation | Reference |
|---------|--------------|----------------|-----------|
| **Interactive Components v2** | Buttons, dropdowns, forms in messages | Use `components` in message tool | [Components](https://docs.openclaw.ai/channels/discord#interactive-components) |
| **Modal Forms** | Pop-up forms for user input | `components.modal` with fields | [Modals](https://docs.openclaw.ai/channels/discord#interactive-components) |
| **Exec Approval Buttons** | Approve/deny dangerous commands via buttons | `channels.discord.execApprovals.enabled: true` | [Exec Approvals](https://docs.openclaw.ai/channels/discord#exec-approvals-in-discord) |
| **Thread-Bound Sessions** | Bind threads to subagent sessions | `/focus`, `/unfocus` commands | [Thread Bindings](https://docs.openclaw.ai/channels/discord#thread-bound-sessions-for-subagents) |

---

## 🎙️ VOICE FEATURES (Advanced)

| Feature | Requirements | Config | Reference |
|---------|--------------|--------|-----------|
| **Voice Channel Join** | Real-time voice conversations | `channels.discord.voice.enabled: true` | [Voice Channels](https://docs.openclaw.ai/channels/discord#voice-channels) |
| **Voice TTS** | Text-to-speech in voice | `voice.tts.provider: "openai"` | [Voice TTS](https://docs.openclaw.ai/channels/discord#voice-channels) |
| ~~Voice Messages (native)~~ | ~~Send audio as voice messages~~ | ~~`asVoice: true`~~ | ~~BROKEN - Issue #16103~~ |
| **Voice Messages (skill)** ✅ | Send audio with waveform | `discord-voice` skill | [discord-voice-skill](https://github.com/chimeraconnor/discord-voice-skill) |

**Note:** Native `asVoice` is broken. Use the custom `discord-voice` skill instead.

### Discord Voice Message Skill (✅ COMPLETED 2026-02-24)

**Repo:** https://github.com/chimeraconnor/discord-voice-skill

**What it does:**
- Sends audio files as native Discord voice messages with waveform visualization
- Works around OpenClaw Issue #16103 (broken native `asVoice`)
- Auto-converts audio to OGG/Opus
- Generates 256-sample waveform from audio amplitude
- 3-step Discord API: Upload URL → CDN Upload → Voice Message

**Usage:**
```bash
~/.openclaw/tools/tts-speak.sh "Hello" /tmp/voice.wav kokoro 1
python3 ~/.openclaw/workspace/skills/discord-voice/scripts/send_voice.py \
  --channel-id 1475566112019058758 \
  --audio-file /tmp/voice.wav
```

**Timing:** ~10-12 seconds total (9-10s TTS + 1-2s processing/upload)

---

## 🔐 ADVANCED ACCESS CONTROL

| Feature | Use Case | Reference |
|---------|----------|-----------|
| **Role-Based Agent Routing** | Different models for different roles | [Role Routing](https://docs.openclaw.ai/channels/discord#role-based-agent-routing) |
| **PluralKit Support** | Handle plural system proxies | [PluralKit](https://docs.openclaw.ai/channels/discord#pluralkit-support) |
| **Channel-Specific Config** | Different settings per channel | [Guild Config](https://docs.openclaw.ai/channels/discord#access-control-and-routing) |
| **DM Policy Control** | Who can DM the bot | [DM Policy](https://docs.openclaw.ai/channels/discord#access-control-and-routing) |

---

## 🛠️ UTILITY FEATURES

| Feature | Command/Config | Reference |
|---------|----------------|-----------|
| **Custom Accent Color** | `ui.components.accentColor: "#5865F2"` | [UI Components](https://docs.openclaw.ai/channels/discord#components-v2-ui) |
| **Forum Channel Auto-Threads** | Send to forum parent | [Forum Channels](https://docs.openclaw.ai/channels/discord#forum-channels) |
| **History Limit Control** | `channels.discord.historyLimit: 20` | [History](https://docs.openclaw.ai/channels/discord#history-context-and-thread-behavior) |
| **Gateway Proxy** | Route through HTTP proxy | [Proxy](https://docs.openclaw.ai/channels/discord#gateway-proxy) |

---

## 📊 RECOMMENDED IMPLEMENTATION ORDER

### Phase 1 (Immediate) - Quality of Life
1. **Live streaming** - See responses being typed in real-time
2. **Ack reaction** - Visual feedback while processing
3. **Bot presence** - Custom status showing you're online

### Phase 2 (This Week) - Interactivity  
4. **Interactive buttons** - For approval workflows
5. **Reply tags** - Better threading
6. **Reaction notifications** - Monitor engagement

### Phase 3 (Later) - Advanced
7. **Voice channels** - Voice conversations
8. **Role-based routing** - Different agents for different user types
9. **Modal forms** - Structured user input

---

## 🔗 KEY DOCUMENTATION LINKS

| Topic | URL |
|-------|-----|
| Discord Setup | https://docs.openclaw.ai/channels/discord |
| Slash Commands | https://docs.openclaw.ai/tools/slash-commands |
| Troubleshooting | https://docs.openclaw.ai/channels/troubleshooting |
| Configuration Reference | https://docs.openclaw.ai/gateway/configuration-reference#discord |
| Sub-agents | https://docs.openclaw.ai/tools/subagents |
| Pairing | https://docs.openclaw.ai/channels/pairing |

---

## NOTES

- Use `openclaw config set <path> <value>` for config changes
- Always restart gateway after config changes: `openclaw gateway restart`
- Check status with: `openclaw channels status --probe`
- View logs with: `openclaw logs --follow`

---

## 🌐 BROWSER AUTOMATION & CONTENT FARMING

### Open-Antigravity Integration

**Goal:** Integrate Open-Antigravity (open-source YK Antigravity fork) into OpenClaw for X.com/Reddit browsing without bans

**What is Open-Antigravity:**
- Leading open-source version of YK Antigravity's browser agent features
- Full browser control via Chrome extension (clicks, scrolls, typing, screenshots, DOM capture, video artifacts)
- VS Code fork: Agent-first IDE with web-native agents that work across editor/terminal/browser
- Universal LLMs: Connects GLM-4.7FlashX, OpenClaw, or any model via gateway
- Agents show cursor movements + record sessions (natural behavior, harder to detect)

**Why it's useful:**
- More human-like browsing patterns (cursor movements, natural scrolling)
- Video recording capabilities for content farming
- Pairs beautifully with searxng MCP for trend spotting
- Automate X/Reddit browsing without getting banned

**Installation:**
```bash
git clone https://github.com/ishandutta2007/open-antigravity
cd open-antigravity
npm install
npm run dev
# Install their Chrome extension
```

**Use Cases:**
- X.com/Reddit content automation
- Trend spotting and monitoring
- Video capture for content creation
- Browser automation that evades detection

**Status:** 📋 Idea/Research Phase
**Priority:** Medium (interesting but not urgent)

---

**Last Updated:** 2026-02-24 (Discord Voice Message skill completed)
