#!/bin/bash
echo "🔧 Fixing Python version (3.14 → 3.11)"

# Remove broken environment
rm -rf .venv
rm poetry.lock

# Create new environment with Python 3.11
python3.11 -m venv .venv

# Activate
source .venv/bin/activate

# Install Poetry
pip install --upgrade pip
pip install poetry

# Install dependencies
poetry install --no-root

echo ""
echo "✅ Python 3.11 environment ready!"
echo "🚀 Run your bot: ./run.sh"
