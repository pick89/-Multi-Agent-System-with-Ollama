#!/bin/bash
# Multi-Agent System - Single Launcher

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Add src to Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

echo "╔════════════════════════════════════╗"
echo "║   🤖 MULTI-AGENT SYSTEM           ║"
echo "║   Production Ready - Clean Version ║"
echo "╚════════════════════════════════════╝"
echo ""

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama is not running${NC}"
    echo "   Start with: ollama serve"
    exit 1
fi

# Show menu
echo "Select mode:"
echo "  1) Telegram Bot (recommended)"
echo "  2) CLI Chat"
echo "  3) Status Check"
echo ""

read -p "Choice [1-3]: " mode

case $mode in
    1)
        echo -e "\n${GREEN}🚀 Starting Telegram bot...${NC}\n"
        poetry run python -m agent_system.main telegram
        ;;
    2)
        echo -e "\n${GREEN}💬 Starting CLI chat...${NC}\n"
        poetry run python -m agent_system.main chat
        ;;
    3)
        echo -e "\n${GREEN}📊 System Status${NC}\n"
        poetry run python -m agent_system.main status
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
