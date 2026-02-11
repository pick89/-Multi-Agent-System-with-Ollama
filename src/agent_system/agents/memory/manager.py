# src/agent_system/memory/manager.py
"""
Simple memory manager for user context
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path
from agent_system.config import settings
from agent_system.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """Simple file-based memory manager"""

    def __init__(self):
        self.memory_dir = settings.MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Memory manager initialized at {self.memory_dir}")

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context from memory"""
        user_file = self.memory_dir / f"user_{user_id}.json"

        if user_file.exists():
            try:
                with open(user_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading user context: {e}")

        return {
            "user_id": user_id,
            "preferred_language": "python",
            "expertise": "beginner",
            "interactions": []
        }

    async def add_interaction(
            self,
            user_id: str,
            user_input: str,
            system_response: str,
            metadata: Dict[str, Any]
    ):
        """Add an interaction to memory"""
        user_file = self.memory_dir / f"user_{user_id}.json"

        # Load existing context
        context = await self.get_user_context(user_id)

        # Add interaction
        if "interactions" not in context:
            context["interactions"] = []

        context["interactions"].append({
            "user_input": user_input[:100],
            "system_response": system_response[:100],
            "metadata": metadata,
            "timestamp": str(import_datetime().now())
        })

        # Keep only last 50 interactions
        if len(context["interactions"]) > 50:
            context["interactions"] = context["interactions"][-50:]

        # Save
        try:
            with open(user_file, 'w') as f:
                json.dump(context, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user context: {e}")


def import_datetime():
    """Import datetime module"""
    from datetime import datetime
    return datetime