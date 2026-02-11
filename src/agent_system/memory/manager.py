"""
Simple memory manager
"""

from typing import Dict, Any, Optional


class MemoryManager:
    """Simple memory manager"""

    def __init__(self):
        pass

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context"""
        return {
            "user_id": user_id,
            "preferred_language": "python",
            "expertise": "beginner"
        }

    async def add_interaction(self, user_id: str, user_input: str, system_response: str, metadata: Dict[str, Any]):
        """Add interaction"""
        pass
