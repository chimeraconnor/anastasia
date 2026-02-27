#!/bin/bash
export XDG_CONFIG_HOME="$HOME/.openclaw/agents/main/qmd/xdg-config"
export XDG_CACHE_HOME="$HOME/.openclaw/agents/main/qmd/xdg-cache"
export PATH="$HOME/.openclaw/workspace/.bun/bin:$PATH"
bun x qmd "$@"
