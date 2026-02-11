"""
Base class for all specialist agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
from agent_system.utils.ollama_client import get_ollama_client
from agent_system.utils.cache import get_cache


class SpecialistAgent(ABC):
    """Abstract base class for all specialist agents"""
    
    def __init__(self, model_name: str):
        self.model = model_name
        self.conversation_history = []
        self.cache = get_cache()
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input and return result"""
        pass
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        temperature: float = 0.7,
        use_cache: bool = True
    ) -> str:
        """Generate response with optional caching"""
        
        # Check cache first for deterministic responses
        if use_cache and temperature < 0.3:
            cached = self.cache.get(self.model, prompt)
            if cached:
                return cached
        
        client = get_ollama_client()
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # Get or create event loop properly
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            should_close = True
        else:
            should_close = False
        
        try:
            response = loop.run_until_complete(
                client.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": temperature}
                )
            )
            result = response["message"]["content"]
            
            # Cache the result
            if use_cache and temperature < 0.3:
                self.cache.set(self.model, prompt, result)
            
            return result
        finally:
            if should_close:
                loop.close()
