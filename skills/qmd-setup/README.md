# QMD Setup Skill

Set up QMD (Quick Markdown Database) for OpenClaw memory in Docker environments.

## Quick Start

**QMD not installed?** Run this skill's setup:

```bash
cd ~/.openclaw/workspace/skills/qmd-setup
# Follow SKILL.md instructions
```

**Estimated time:** 5-10 minutes (downloads bun, QMD, tsx, sets up environment)

## What is QMD?

QMD is a **local semantic search system** for OpenClaw memory:
- Uses local AI models (Gemma 300M) - no API keys!
- Runs completely offline
- Hybrid search: BM25 (keywords) + vectors (semantic) + reranking
- Auto-indexes your memory files (MEMORY.md, memory/**/*.md, sessions/**/*.md)

## Why This Skill?

Setting up QMD in Docker is tricky because:
1. System paths (`/usr/local`, `~/.npm`) don't persist
2. Standard bun installs fail with permission errors
3. Models symlink often breaks after container restarts
4. Need persistent workspace paths

This skill provides the complete Docker-aware setup that survives restarts.

## Features

✅ **Persistent installation** - Uses workspace-local paths
✅ **Automatic dependencies** - Downloads bun, QMD, tsx
✅ **Symlink fix** - Corrects broken models link
✅ **Wrapper script** - Sets up XDG environment automatically
✅ **Docker-optimized** - All paths persist across container restarts

## Installation Output

After setup, you'll have:
```
~/.local/bin/qmd          ← Main QMD binary (wrapper script)
~/.openclaw/workspace/.bun/  ← Bun installation (persists)
~/.openclaw/agents/main/qmd/   ← QMD config & database (persists)
~/.bun/install/cache/        ← QMD models cache (auto-downloads)
```

## Usage

Once installed, add to OpenClaw config:
```json
{
  "memory": {
    "backend": "qmd"
  }
}
```

Then test with:
```bash
qmd query "what did we learn about docker?"
qmd collection list
```

## Documentation

See [SKILL.md](SKILL.md) for complete documentation.

---

**Author:** Anastasia Steele
