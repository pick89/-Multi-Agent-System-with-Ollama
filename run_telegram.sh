#!/bin/bash
# One-line Telegram bot launcher

echo "🚀 Starting Multi-Agent Telegram Bot..."
echo "====================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root!"
    exit 1
fi

# Check Ollama
echo -n "🔍 Checking Ollama... "
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅"
else
    echo "❌"
    echo "❌ Ollama is not running!"
    echo "💡 Start with: ollama serve"
    exit 1
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "💡 Create it with: cp .env.example .env"
    exit 1
fi

# Check Telegram token
if grep -q "TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here" .env; then
    echo "❌ Telegram token not configured!"
    echo "💡 Edit .env and add your token from @BotFather"
    exit 1
fi

# Check if we're in poetry shell
if [ -z "$POETRY_ACTIVE" ]; then
    echo "🔍 Using poetry run..."
    POETRY_CMD="poetry run"
else
    POETRY_CMD=""
fi

# Launch bot
echo "✅ Everything ready!"
echo "📱 Starting bot... Press Ctrl+C to stop"
echo ""

$POETRY_CMD python -m agent_system.main telegram
