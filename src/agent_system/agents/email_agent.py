"""
Email agent placeholder
"""

from typing import Dict, Any
from agent_system.core.specialist_base import SpecialistAgent


class EmailAgent(SpecialistAgent):
    """Placeholder for email agent"""

    def __init__(self, model_name: str):
        super().__init__(model_name)

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": "Email agent not fully implemented yet.",
            "model_used": self.model,
            "actions": []
        }
