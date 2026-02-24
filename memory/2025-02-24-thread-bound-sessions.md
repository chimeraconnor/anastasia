# Thread-Bound Sessions Implementation

**Date:** 2025-02-24
**Status:** ✅ ACTIVE

## Overview
Enabled Discord Thread-Bound Sessions feature allowing threads to be bound to specific subagent sessions for persistent context.

## Configuration Added

### Global Settings
```json
"session": {
  "threadBindings": {
    "enabled": true,
    "ttlHours": 24
  }
}
```

### Discord-Specific Settings
```json
"channels": {
  "discord": {
    "threadBindings": {
      "enabled": true,
      "spawnSubagentSessions": true,
      "ttlHours": 24
    }
  }
}
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/focus <target>` | Bind current thread to a subagent/session target |
| `/unfocus` | Remove the thread binding |
| `/agents` | Show active subagents and binding state |
| `/session ttl <duration\|off>` | Update auto-unfocus TTL |

## Use Cases

1. **Dedicated Project Threads** - Each project gets its own subagent with full context
2. **Long-running Tasks** - Bind a thread to a subagent and return hours later
3. **Specialized Assistants** - Create threads for specific roles (coding, research, etc.)

## How It Works

1. Create a Discord thread in any allowed channel
2. Use `/focus <agent-id>` to bind the thread to a subagent
3. All subsequent messages in that thread route to the same session
4. Binding auto-expires after 24 hours of inactivity (configurable)
5. Use `/unfocus` to manually release the binding

## Files Modified
- `/home/node/.openclaw/openclaw.json`

## Notes
- Auto-unfocus TTL resets on each new message in the thread
- `spawnSubagentSessions: true` enables automatic thread creation for `sessions_spawn({ thread: true })`
- Works with existing Discord allowlist/guild configuration
