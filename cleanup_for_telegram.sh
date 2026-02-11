#!/bin/bash
# cleanup_for_telegram.sh - Clean and prepare for Telegram

echo "🧹 Cleaning up for Telegram deployment..."

# 1. Remove debug/test files we don't need
rm -f test_router*.py
rm -f chat_fast*.py
rm -f chat_instant*.py
rm -f fix_*.sh
rm -f diagnose.py
rm -f complete_fix.sh

# 2. Create clean directory structure
mkdir -p src/agent_system/telegram
mkdir -p data/logs
mkdir -p data/memory

# 3. Create clean __init__.py files
touch src/agent_system/telegram/__init__.py
touch src/agent_system/telegram/bot.py
touch src/agent_system/telegram/handlers.py
touch src/agent_system/telegram/callbacks.py
touch src/agent_system/telegram/keyboards.py

# 4. Disable debug logging permanently
cat > src/agent_system/utils/logger.py << 'EOF'
"""Clean logging configuration - NO DEBUG SPAM"""

import logging
import sys
from pathlib import Path
from loguru import logger
from agent_system.config import settings

# Disable all HTTP debug logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

def setup_logging(verbose: bool = False):
    logger.remove()
    log_level = "INFO"  # Always INFO, no DEBUG spam

    logger.add(sys.stdout, format="<level>{message}</level>", level=log_level, colorize=True)

    log_file = settings.LOGS_DIR / "agent_system.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.add(log_file, format="{time} | {level} | {message}", level="INFO", rotation="10 MB")

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.WARNING, force=True)

def get_logger(name: str):
    return logger.bind(name=name)
EOF

echo "✅ Cleanup complete!"
EOF

chmod +x cleanup_for_telegram.sh
./cleanup_for_telegram.sh