#!/bin/bash
# Model deployment script for Ollama

set -e

echo "🚀 Multi-Agent System - Model Deployment"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Model tiers
TIER1=("gemma3:1b" "gemma3:4b" "qwen2.5-coder:3b" "qwen2.5-coder:7b" "phi4:14b")
TIER2=("llama3.2-vision:11b" "minicpm-v:8b" "aya:8b" "nous-hermes2:10.7b" "mistral-nemo:12b" "qwen2.5:14b")
TIER3=("gemma3:12b" "qwen2.5:32b" "deepseek-coder-v2:16b" "command-r:35b")

# Check if Ollama is running
check_ollama() {
  echo -n "Checking Ollama connection... "
  if curl -s http://localhost:11434/api/tags >/dev/null; then
    echo -e "${GREEN}OK${NC}"
    return 0
  else
    echo -e "${RED}FAILED${NC}"
    echo "❌ Ollama is not running. Start it with: ollama serve"
    return 1
  fi
}

# Deploy models
deploy_tier() {
  local tier_name=$1
  shift
  local models=("$@")

  echo -e "\n${BLUE}📦 Deploying $tier_name models (${#models[@]} models)${NC}"

  for model in "${models[@]}"; do
    echo -n "  Pulling $model... "
    if ollama pull "$model" >/dev/null 2>&1; then
      echo -e "${GREEN}✓${NC}"
    else
      echo -e "${RED}✗${NC}"
      echo "  ❌ Failed to pull $model"
    fi
  done
}

# Show model info
show_info() {
  echo -e "\n${BLUE}📊 Deployed Models${NC}"
  ollama list
}

# Main
main() {
  # Check Ollama
  check_ollama || exit 1

  # Show menu
  echo -e "\nSelect deployment tier:"
  echo "1) Essential (${#TIER1[@]} models) - Router + Core capabilities"
  echo "2) Extended (${#TIER2[@]} models) - Vision + Multilingual"
  echo "3) Maximum (${#TIER3[@]} models) - High-quality models"
  echo "4) All models"
  echo "5) Custom selection"

  read -p "Choice [1-5]: " choice

  case $choice in
  1) deploy_tier "Essential" "${TIER1[@]}" ;;
  2) deploy_tier "Extended" "${TIER2[@]}" ;;
  3) deploy_tier "Maximum" "${TIER3[@]}" ;;
  4)
    deploy_tier "Essential" "${TIER1[@]}"
    deploy_tier "Extended" "${TIER2[@]}"
    deploy_tier "Maximum" "${TIER3[@]}"
    ;;
  5)
    echo "Available models:"
    all_models=("${TIER1[@]}" "${TIER2[@]}" "${TIER3[@]}")
    for i in "${!all_models[@]}"; do
      echo "  $((i + 1))) ${all_models[$i]}"
    done
    read -p "Enter model numbers (space-separated): " -a selections
    for idx in "${selections[@]}"; do
      deploy_tier "Custom" "${all_models[$((idx - 1))]}"
    done
    ;;
  *)
    echo -e "${RED}Invalid choice${NC}"
    exit 1
    ;;
  esac

  show_info
  echo -e "\n${GREEN}✅ Deployment complete!${NC}"
}

main
