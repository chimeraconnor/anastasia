---
name: qmd-setup
description: Set up QMD (local semantic search) for OpenClaw memory. Use when: (1) QMD is not installed or broken, (2) Setting up memory backend for the first time, (3) Docker container needs persistent QMD installation, (4) Diagnosing QMD errors, (5) Configuring OpenClaw to use QMD as memory backend.
metadata:
  openclaw:
    emoji: "🧠"
    requires:
      bins: ["bash", "curl", "chmod", "mkdir", "ln", "find"]
---

# QMD Setup Skill

Set up QMD (Quick Markdown Database) as a local semantic search backend for OpenClaw memory. QMD uses local AI models (Gemma 300M via node-llama-cpp) - no API keys needed, runs entirely offline.

## What is QMD?

QMD is a **local-first semantic search system** that:
- Scans your memory files (MEMORY.md, memory/**/*.md, sessions/**/*.md)
- Chunks text into smaller pieces
- Generates embeddings using **node-llama-cpp** (Gemma 300M model)
- Stores in SQLite with sqlite-vec for fast similarity search
- Provides hybrid search: BM25 (keywords) + vectors (semantic) + reranking
- Works completely offline - no API keys or external services required

## Docker-Specific Challenges

When running OpenClaw in Docker, QMD setup has special challenges:

1. **Permissions** - Can't write to system paths (/usr/local, ~/.npm), need workspace-local paths
2. **Persistence** - Installations in `/tmp` or `/home/node` vanish on container restart
3. **Bun availability** - Default install locations for bun may not work in Docker
4. **Symlink confusion** - XDG paths may point to non-existent directories after restarts

## Quick Setup (Persistent Installation)

This installation persists across Docker restarts by using workspace-local paths.

### Step 1: Install Bun

Bun is required to run QMD. Install it to workspace, not system paths.

```bash
# Install bun to workspace (persistent)
curl -fsSL https://bun.sh/install | \
  BUN_INSTALL="$HOME/.openclaw/workspace/.bun" bash

# Verify installation
/home/node/.openclaw/workspace/.bun/bin/bun --version
```

### Step 2: Create Persistent Directories

```bash
# Create bun installation directory
mkdir -p "$HOME/.openclaw/workspace/.bun"

# Create QMD models cache directory (QMD auto-downloads models here)
mkdir -p "$HOME/.cache/qmd/models"

# Create local binaries directory
mkdir -p "$HOME/.local/bin"
```

### Step 3: Install QMD via Bun

```bash
# Add bun to PATH and install QMD globally (to workspace)
export PATH="$HOME/.openclaw/workspace/.bun/bin:$PATH"
bun install -g qmd

# Note: This installs to ~/.bun/install/global/ which persists in Docker
```

### Step 4: Install tsx (Required by QMD)

QMD requires tsx to run TypeScript:

```bash
export PATH="$HOME/.openclaw/workspace/.bun/bin:$PATH"
bun add -g tsx

# Note: Also installs to ~/.bun/install/global/
```

### Step 5: Fix Models Symlink (Critical!)

The XDG models symlink is often broken. Fix it:

```bash
# Remove broken symlink
rm -f ~/.openclaw/agents/main/qmd/xdg-cache/qmd/models

# Create symlink to QMD's actual cache
ln -sf ~/.bun/install/cache ~/.openclaw/agents/main/qmd/xdg-cache/qmd/models

# Verify
ls -la ~/.openclaw/agents/main/qmd/xdg-cache/qmd/models
```

**Why this matters:** If this symlink is broken, QMD can't find/load embedding models (Gemma 300M) and will fail silently or throw errors.

### Step 6: Create QMD Runner Script

Create a wrapper script that sets up the correct environment:

```bash
cat > "$HOME/.local/bin/qmd" << 'EOF'
#!/bin/bash
# QMD Runner - Sets up XDG environment for OpenClaw
# This ensures QMD finds its config and models correctly

# Set XDG environment variables (required by OpenClaw)
export XDG_CONFIG_HOME="$HOME/.openclaw/agents/main/qmd/xdg-config"
export XDG_CACHE_HOME="$HOME/.openclaw/agents/main/qmd/xdg-cache"

# Add bun to PATH (in case tsx needs it)
export PATH="$HOME/.openclaw/workspace/.bun/bin:$PATH"

# Execute qmd with all arguments passed to this script
cd ~/.bun/install/global/node_modules/@tobilu/qmd
exec bun run qmd "$@"
EOF

chmod +x "$HOME/.local/bin/qmd"
```

### Step 7: Verify Installation

```bash
# Check QMD version
"$HOME/.local/bin/qmd" --version
# Should output: qmd 1.1.0

# Check collections
"$HOME/.local/bin/qmd" collection list
# Should show: memory-root-main, memory-alt-main, memory-dir-main, sessions-main

# Test search
"$HOME/.local/bin/qmd" query "test"
# Should search memory files
```

## OpenClaw Configuration

Once QMD is installed, configure OpenClaw to use it:

```json
{
  "memory": {
    "backend": "qmd",
    "qmd": {
      "includeDefaultMemory": true,
      "update": {
        "interval": "5m"
      }
    }
  }
}
```

**Key config options:**
- `includeDefaultMemory: true` - Auto-index MEMORY.md and memory/**/*.md
- `update.interval` - How often to refresh embeddings (default 5 minutes)
- `paths[]` - Add custom directories to index
- `sessions` - Enable session JSONL indexing

## Environment Variables (Set by Runner Script)

QMD requires these XDG variables (OpenClaw sets these automatically if configured):

```bash
export XDG_CONFIG_HOME="$HOME/.openclaw/agents/main/qmd/xdg-config"
export XDG_CACHE_HOME="$HOME/.openclaw/agents/main/qmd/xdg-cache"
```

**What they do:**
- `XDG_CONFIG_HOME` - Points to config file (collections definition)
- `XDG_CACHE_HOME` - Points to cache (SQLite database, models, embeddings)

## Common Issues & Troubleshooting

### "qmd: Permission denied" or "Command not found"

**Cause:** Binary not in PATH or not executable

**Fix:** Ensure wrapper script sets PATH correctly:
```bash
export PATH="$HOME/.openclaw/workspace/.bun/bin:$PATH"
```

### "No embeddings found in QMD database"

**Cause:** First time use, models not downloaded

**Fix:** QMD auto-downloads models on first query. Or manually trigger:
```bash
export XDG_CONFIG_HOME="$HOME/.openclaw/agents/main/qmd/xdg-config"
export XDG_CACHE_HOME="$HOME/.openclaw/agents/main/qmd/xdg-cache"
qmd query "test"
```

### Broken models symlink

**Cause:** Symlink points to `/home/node/.cache/qmd/models` which doesn't exist

**Fix:**
```bash
rm -f ~/.openclaw/agents/main/qmd/xdg-cache/qmd/models
ln -sf ~/.bun/install/cache ~/.openclaw/agents/main/qmd/xdg-cache/qmd/models
```

### "sh: 1: qmd: Permission denied"

**Cause:** bun can't execute due to Docker permissions

**Fix:** Use wrapper script that changes directory first:
```bash
cd ~/.bun/install/global/node_modules/@tobilu/qmd
exec bun run qmd "$@"
```

## Docker Persistence Notes

**Critical for Docker environments:**

1. **Don't install to system paths** (`/usr/local`, `~/.npm`) - they're lost on restart
2. **Use workspace volume** - `~/.openclaw/workspace/` persists across restarts
3. **Avoid `/tmp`** - Installations there vanish
4. **Model downloads** - Happen automatically to `~/.bun/install/cache/`, symlink points there
5. **Config files** - OpenClaw's QMD config at `~/.openclaw/agents/main/qmd/xdg-config/` persists

## How It Works

### QMD Startup (Automatic)

1. OpenClaw starts → initializes QMD manager
2. Sets XDG_CONFIG_HOME and XDG_CACHE_HOME automatically
3. Reads collections from `~/.openclaw/agents/main/qmd/xdg-config/qmd/index.yml`
4. Runs background update timers (default: every 5 minutes)
5. QMD auto-downloads models (Gemma 300M) on first query to `~/.bun/install/cache/`
6. Generates embeddings locally using node-llama-cpp
7. Stores in SQLite: `~/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite`

### Search Flow

When you ask a memory search:

1. User queries: "What did we learn about time zones?"
2. OpenClaw → QMD: `qmd query "time zones"`
3. QMD:
   - Searches BM25 (keyword matching)
   - Searches vectors (semantic similarity)
   - Reranks and combines results
4. Returns: Ranked results with file paths, line numbers, snippets
5. OpenClaw displays: Formatted search results with citations

## Quick Reference

| Command | Purpose |
|---------|---------|
| `qmd query <text>` | Hybrid search (BM25 + vectors + reranking) - recommended |
| `qmd search <text>` | Full-text BM25 keywords (no LLM) |
| `qmd vsearch <text>` | Vector similarity only |
| `qmd get <file>` | Show a single document |
| `qmd multi-get <pattern>` | Batch fetch files |
| `qmd collection list` | See indexed collections |
| `qmd collection add <path>` | Add directory to index |
| `qmd context add <text>` | Add manual summary/context |

## Memory Dashboard Integration

The Memory Dashboard at `tools/memory-dashboard/` visualizes QMD embeddings as an interactive 3D graph. It reads from the same SQLite database that QMD writes to.

**Dashboard location:** `~/.openclaw/workspace/tools/memory-dashboard/dashboard.html`

**Open in browser:** `file:///home/node/.openclaw/workspace/tools/memory-dashboard/dashboard.html`

## When to Use This Skill

Use this skill when:
- **QMD is missing** - `which qmd` returns nothing
- **QMD errors** - "Permission denied", "Command not found", or "No embeddings found"
- **Setting up Docker** - Need persistent installation that survives restarts
- **Broken symlinks** - Models symlink points to wrong location
- **First-time setup** - Never configured QMD before
- **Diagnosing issues** - Figure out why QMD isn't working

**Ask the user:**
"QMD is a local-first semantic search system. It needs to be downloaded and installed. Can I set it up with persistent paths that survive Docker restarts? I'll need bun and a few minutes to complete."

## Installation Workflow Summary

```bash
# 1. Install Bun
curl -fsSL https://bun.sh/install | \
  BUN_INSTALL="$HOME/.openclaw/workspace/.bun" bash

# 2. Install QMD + tsx
export PATH="$HOME/.openclaw/workspace/.bun/bin:$PATH"
bun install -g qmd
bun add -g tsx

# 3. Fix models symlink
rm -f ~/.openclaw/agents/main/qmd/xdg-cache/qmd/models
ln -sf ~/.bun/install/cache ~/.openclaw/agents/main/qmd/xdg-cache/qmd/models

# 4. Create runner script
cat > "$HOME/.local/bin/qmd" << 'EOF'
#!/bin/bash
export XDG_CONFIG_HOME="$HOME/.openclaw/agents/main/qmd/xdg-config"
export XDG_CACHE_HOME="$HOME/.openclaw/agents/main/qmd/xdg-cache"
export PATH="$HOME/.openclaw/workspace/.bun/bin:$PATH"
cd ~/.bun/install/global/node_modules/@tobilu/qmd
exec bun run qmd "$@"
EOF
chmod +x "$HOME/.local/bin/qmd"

# 5. Verify
"$HOME/.local/bin/qmd" --version
"$HOME/.local/bin/qmd" collection list
```

## Key Takeaways

- **Persistent paths matter** - Use `~/.openclaw/workspace/` not system paths
- **Fix the models symlink** - It's the most common failure point
- **Wrapper scripts** - Essential for setting up environment variables
- **XDG directories** - Required for QMD to find config and cache
- **Docker persistence** - Everything in `~/.openclaw/` and `~/.bun/` survives restarts

---

**Author:** Anastasia Steele
**Based on:** Real-world troubleshooting in OpenClaw Docker environment
**License:** MIT
