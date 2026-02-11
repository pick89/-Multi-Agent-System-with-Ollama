"""
Generic agent for general tasks and conversations
"""

from typing import Dict, Any, Optional
from agent_system.core.specialist_base import SpecialistAgent


class GenericAgent(SpecialistAgent):
    """Generic agent for general conversations and tasks"""
    
    def __init__(self, model_name: str):
        super().__init__(model_name)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process general requests and conversations"""
        task = input_data.get("task", "")
        
        # Create appropriate system prompt based on task
        system_prompt = """You are a helpful, friendly assistant. 
        Provide clear, concise, and natural responses. 
        Be conversational and engaging.
        If you don't know something, say so honestly."""
        
        # Generate response using the model
        try:
            response = self.generate(task, system_prompt, temperature=0.7)
            
            return {
                "response": response,
                "model_used": self.model,
                "actions": []
            }
        except Exception as e:
            # Fallback response if generation fails
            return {
                "response": "Hello! How can I help you today?",
                "model_used": self.model,
                "actions": []
            }
