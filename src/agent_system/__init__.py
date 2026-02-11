"""
Multi-Agent System with Ollama and Telegram Integration
"""

__version__ = "0.1.0"

# Only import absolutely essential items
# Don't import telegram modules here - they cause circular imports
from agent_system.config import settings

__all__ = ["settings"]
