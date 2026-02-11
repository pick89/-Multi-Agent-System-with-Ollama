#!/bin/bash
# Multi-Agent System - Complete Diagnostic Tool

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

echo "${BOLD}╔════════════════════════════════════════════════════════╗${NC}"
echo "${BOLD}║     MULTI-AGENT SYSTEM - COMPLETE DIAGNOSTIC         ║${NC}"
echo "${BOLD}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0
WARNINGS=0

# ---------------------------------------------------------------------------
# 1. PYTHON ENVIRONMENT
# ---------------------------------------------------------------------------
echo "${BOLD}📌 PYTHON ENVIRONMENT${NC}"
echo "──────────────────────────────────────────────────"

# Python version
PY_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
if [[ $PY_VERSION == 3.11* ]]; then
    echo "  ${GREEN}✅ Python: $PY_VERSION${NC}"
else
    echo "  ${RED}❌ Python: $PY_VERSION (need 3.11.x)${NC}"
    ((ERRORS++))
fi

# Virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "  ${GREEN}✅ Virtual env: $(basename $VIRTUAL_ENV)${NC}"
else
    echo "  ${YELLOW}⚠️  Virtual env: Not activated${NC}"
    ((WARNINGS++))
fi

# PYTHONPATH
if [[ $PYTHONPATH == *"src"* ]]; then
    echo "  ${GREEN}✅ PYTHONPATH: contains ./src${NC}"
else
    echo "  ${YELLOW}⚠️  PYTHONPATH: ./src not set${NC}"
    ((WARNINGS++))
fi

echo ""

# ---------------------------------------------------------------------------
# 2. PROJECT STRUCTURE
# ---------------------------------------------------------------------------
echo "${BOLD}📁 PROJECT STRUCTURE${NC}"
echo "──────────────────────────────────────────────────"

# Check critical directories
declare -a DIRS=(
    "src/agent_system"
    "src/agent_system/telegram"
    "src/agent_system/core"
    "src/agent_system/utils"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ${GREEN}✅ $dir${NC}"
    else
        echo "  ${RED}❌ $dir${NC}"
        ((ERRORS++))
    fi
done

# Check critical files
declare -a FILES=(
    "src/agent_system/__init__.py"
    "src/agent_system/main.py"
    "src/agent_system/config.py"
    "src/agent_system/telegram/bot.py"
    "src/agent_system/core/__init__.py"
    "src/agent_system/utils/__init__.py"
    ".env"
    "pyproject.toml"
    "run.sh"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ${GREEN}✅ $file${NC}"
    else
        echo "  ${RED}❌ $file${NC}"
        ((ERRORS++))
    fi
done

echo ""

# ---------------------------------------------------------------------------
# 3. OLLAMA
# ---------------------------------------------------------------------------
echo "${BOLD}🦙 OLLAMA${NC}"
echo "──────────────────────────────────────────────────"

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "  ${GREEN}✅ Ollama service: Running${NC}"
    
    # Get model count
    MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name"' | wc -l)
    echo "  ${GREEN}✅ Models installed: $MODELS${NC}"
    
    # Check for required models
    REQUIRED_MODELS=("phi4:14b" "gemma3:1b" "qwen2.5-coder:3b")
    for model in "${REQUIRED_MODELS[@]}"; do
        if curl -s http://localhost:11434/api/tags | grep -q "$model"; then
            echo "  ${GREEN}✅ Model: $model${NC}"
        else
            echo "  ${YELLOW}⚠️  Model: $model not found${NC}"
            ((WARNINGS++))
        fi
    done
else
    echo "  ${RED}❌ Ollama service: Not running${NC}"
    ((ERRORS++))
fi

echo ""

# ---------------------------------------------------------------------------
# 4. CONFIGURATION
# ---------------------------------------------------------------------------
echo "${BOLD}🔧 CONFIGURATION${NC}"
echo "──────────────────────────────────────────────────"

# Check .env file
if [ -f ".env" ]; then
    # Check for Telegram token
    if grep -q "TELEGRAM_BOT_TOKEN=[A-Za-z0-9:_-]\{40,\}" .env; then
        TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d'=' -f2 | cut -c1-10)
        echo "  ${GREEN}✅ Telegram token: ${TOKEN}...${NC}"
    else
        echo "  ${RED}❌ Telegram token: Missing or invalid${NC}"
        ((ERRORS++))
    fi
    
    # Check for PYTHONPATH in .env (should NOT be there)
    if grep -q "PYTHONPATH" .env; then
        echo "  ${YELLOW}⚠️  PYTHONPATH in .env - REMOVE THIS!${NC}"
        ((WARNINGS++))
    else
        echo "  ${GREEN}✅ .env clean (no PYTHONPATH)${NC}"
    fi
else
    echo "  ${RED}❌ .env file missing${NC}"
    ((ERRORS++))
fi

echo ""

# ---------------------------------------------------------------------------
# 5. PYTHON IMPORTS
# ---------------------------------------------------------------------------
echo "${BOLD}📦 PYTHON IMPORTS${NC}"
echo "──────────────────────────────────────────────────"

# Create temp Python script
cat > /tmp/test_imports.py << 'PYEOF'
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("  Testing imports...")

modules = [
    "agent_system",
    "agent_system.config",
    "agent_system.main",
    "agent_system.telegram.bot",
    "agent_system.core",
    "agent_system.utils",
]

for module in modules:
    try:
        __import__(module)
        print(f"  ✅ {module}")
    except ImportError as e:
        print(f"  ❌ {module} - {str(e)[:50]}")
        sys.exit(1)

print("  ✅ All imports successful!")
PYEOF

cd /home/bwb/Dev/Ai/multi-agent-system
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
python /tmp/test_imports.py
if [ $? -eq 0 ]; then
    echo "  ${GREEN}✅ Python imports: OK${NC}"
else
    echo "  ${RED}❌ Python imports: Failed${NC}"
    ((ERRORS++))
fi

echo ""

# ---------------------------------------------------------------------------
# 6. TELEGRAM BOT
# ---------------------------------------------------------------------------
echo "${BOLD}📱 TELEGRAM BOT${NC}"
echo "──────────────────────────────────────────────────"

# Check if we can import the bot class
cat > /tmp/test_telegram.py << 'PYEOF'
import sys
from pathlib import Path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
try:
    from agent_system.telegram.bot import TelegramBot
    print("✅ TelegramBot class imported")
except Exception as e:
    print(f"❌ {str(e)[:100]}")
    sys.exit(1)
PYEOF

python /tmp/test_telegram.py
if [ $? -eq 0 ]; then
    echo "  ${GREEN}✅ Telegram bot class: OK${NC}"
else
    echo "  ${RED}❌ Telegram bot class: Failed${NC}"
    ((ERRORS++))
fi

# Check for running bot instances
BOT_PIDS=$(pgrep -f "python.*agent_system.*telegram")
if [ -n "$BOT_PIDS" ]; then
    echo "  ${YELLOW}⚠️  Bot already running (PID: $BOT_PIDS)${NC}"
    echo "     Run 'pkill -f \"python.*agent_system.*telegram\"' to stop"
    ((WARNINGS++))
else
    echo "  ${GREEN}✅ No conflicting bot instances${NC}"
fi

echo ""

# ---------------------------------------------------------------------------
# 7. MEMORY & SWAP
# ---------------------------------------------------------------------------
echo "${BOLD}💾 MEMORY & SWAP${NC}"
echo "──────────────────────────────────────────────────"

# RAM
RAM_TOTAL=$(free -h | grep Mem | awk '{print $2}')
RAM_AVAIL=$(free -h | grep Mem | awk '{print $7}')
RAM_PERCENT=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')

if [ $RAM_PERCENT -lt 80 ]; then
    echo "  ${GREEN}✅ RAM: $RAM_AVAIL / $RAM_TOTAL ($RAM_PERCENT%)${NC}"
else
    echo "  ${YELLOW}⚠️  RAM: $RAM_AVAIL / $RAM_TOTAL ($RAM_PERCENT% used)${NC}"
    ((WARNINGS++))
fi

# Swap
SWAP_TOTAL=$(free -h | grep Swap | awk '{print $2}')
SWAP_FREE=$(free -h | grep Swap | awk '{print $4}')
SWAP_PERCENT=$(free | grep Swap | awk '{printf "%.0f", $3/$2 * 100}' 2>/dev/null || echo "0")

if [ "$SWAP_TOTAL" != "0B" ]; then
    echo "  ${GREEN}✅ Swap: $SWAP_FREE / $SWAP_TOTAL ($SWAP_PERCENT% used)${NC}"
fi

echo ""

# ---------------------------------------------------------------------------
# 8. SUMMARY
# ---------------------------------------------------------------------------
echo "${BOLD}📊 DIAGNOSTIC SUMMARY${NC}"
echo "──────────────────────────────────────────────────"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "${GREEN}✅ PERFECT! No errors, no warnings.${NC}"
    echo "${GREEN}✅ Your system is 100% ready!${NC}"
elif [ $ERRORS -eq 0 ] && [ $WARNINGS -gt 0 ]; then
    echo "${YELLOW}⚠️  $WARNINGS warnings, 0 errors${NC}"
    echo "${YELLOW}⚠️  System will work but has room for improvement${NC}"
elif [ $ERRORS -gt 0 ]; then
    echo "${RED}❌ $ERRORS errors, $WARNINGS warnings${NC}"
    echo "${RED}❌ Please fix errors before running${NC}"
fi

echo ""
echo "${BOLD}📋 NEXT STEPS:${NC}"
echo "──────────────────────────────────────────────────"
if [ $ERRORS -eq 0 ]; then
    echo "  ${GREEN}1. Run your bot: ./run.sh${NC}"
    echo "  ${GREEN}2. Test Telegram: /start${NC}"
    echo "  ${GREEN}3. Test CLI: poetry run python -m agent_system.main chat${NC}"
else
    echo "  ${YELLOW}Fix the errors above, then run this script again${NC}"
fi
echo ""

exit $ERRORS
