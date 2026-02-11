#!/bin/bash
# Run bot with swap optimization

echo "🚀 Starting Bot with Swap Optimization..."
echo "========================================="

# Set swap to maximum aggressiveness
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=5m

# Force Ollama to use swap
sudo sysctl -w vm.swappiness=100 > /dev/null 2>&1

# Clear caches
sudo sync && sudo sysctl -w vm.drop_caches=3 > /dev/null 2>&1

# Show memory status
echo "💾 Memory Status:"
free -h | head -2
echo ""

# Start bot
poetry run python -m agent_system.main telegram
