"""Multi-Agent System with Ollama and Telegram Integration"""

__version__ = "0.1.0"
__author__ = "Your Name"

from agent_system.config import Settings
from agent_system.core.orchestrator import AgentOrchestrator
from agent_system.telegram.bot import TelegramAgentBot

__all__ = [
    "Settings",
    "AgentOrchestrator",
    "TelegramAgentBot",
]
