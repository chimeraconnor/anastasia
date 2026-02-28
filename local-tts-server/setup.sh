#!/bin/bash
set -e

echo "🎙️ Local TTS Server Setup"
echo "========================"

# Check if we're in the right directory
if [ ! -f "server.js" ]; then
    echo "❌ Error: Run this script from local-tts-server directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Test if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not installed"
    exit 1
fi

# Test if anastasia-tts skill exists
TTS_SCRIPT="/home/node/.openclaw/workspace/skills/anastasia-tts/scripts/anastasia-speak.py"
if [ ! -f "$TTS_SCRIPT" ]; then
    echo "❌ Error: anastasia-tts skill not found at $TTS_SCRIPT"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""
echo "🎯 Setup complete!"
echo ""
echo "To start the server:"
echo "  npm start"
echo ""
echo "To run as a service with PM2:"
echo "  npm install -g pm2"
echo "  pm2 start server.js --name local-tts"
echo ""
echo "To configure OpenClaw Discord voice:"
echo "  openclaw config set channels.discord.voice.tts.provider openai"
echo "  openclaw config set channels.discord.voice.tts.openai.baseUrl 'http://localhost:3456'"
echo "  openclaw config set channels.discord.voice.tts.openai.apiKey 'local'"
echo ""
echo "Then restart OpenClaw Gateway:"
echo "  openclaw gateway restart"
