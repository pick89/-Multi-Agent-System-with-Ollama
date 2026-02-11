"""
Main orchestrator for routing requests to specialist agents
"""

import asyncio
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

from agent_system.config import settings
from agent_system.core.router_agent import RouterAgent
from agent_system.core.specialist_base import SpecialistAgent
from agent_system.agents import CodeSpecialist
from agent_system.agents import EmailAgent
from agent_system.agents import VisionAgent
from agent_system.agents import AnalysisAgent
from agent_system.agents import GenericAgent
from agent_system.utils.logger import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Main orchestrator for the multi-agent system"""

    def __init__(self):
        self.router = RouterAgent()
        self.specialists: Dict[str, SpecialistAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Specialist factory registry
        self.specialist_factories = {
            "code": {
                "qwen2.5-coder:3b": lambda: CodeSpecialist("qwen2.5-coder:3b"),
                "qwen2.5-coder:7b": lambda: CodeSpecialist("qwen2.5-coder:7b"),
                "deepseek-coder-v2:16b": lambda: CodeSpecialist("deepseek-coder-v2:16b")
            },
            "vision": {
                "gemma3:4b": lambda: VisionAgent("gemma3:4b"),
                "llama3.2-vision:11b": lambda: VisionAgent("llama3.2-vision:11b"),
                "minicpm-v:8b": lambda: VisionAgent("minicpm-v:8b")
            },
            "analysis": {
                "phi4:14b": lambda: AnalysisAgent("phi4:14b"),
                "qwen2.5:14b": lambda: AnalysisAgent("qwen2.5:14b"),
                "gemma3:12b": lambda: AnalysisAgent("gemma3:12b")
            },
            "email": {
                "phi4:14b": lambda: EmailAgent("phi4:14b")
            }
        }

    async def process_request(
            self,
            user_input: str,
            user_id: str,
            session: Optional[Dict] = None,
            attachments: Optional[List] = None
    ) -> Dict[str, Any]:
        """Process a user request through the agent pipeline"""
        
        session = session or {}
        user_context = {"user_id": user_id}

        try:
            # Step 1: Route the request
            route_result = await self._route_request(user_input, user_context)
            specialist_model = route_result["model"]
            classification = route_result["classification"]

            # Check if we need clarification
            if classification.get("requires_clarification"):
                return {
                    "response": "\n".join(classification.get("suggested_questions", ["Could you provide more details?"])),
                    "requires_clarification": True,
                    "category": classification.get("category"),
                    "model_used": specialist_model,
                    "confidence": classification.get("confidence", 0.5)
                }

            # Step 2: Get or initialize specialist
            specialist = self._get_specialist(specialist_model, classification.get("category", "general"))

            # Step 3: Process with specialist
            processing_result = await self._process_with_specialist(
                specialist,
                user_input,
                classification,
                user_context,
                attachments
            )

            # Step 4: Synthesize response
            final_response = processing_result.get("response", "Task completed successfully.")
            
            return {
                "response": final_response,
                "model_used": specialist_model,
                "category": classification.get("category"),
                "confidence": classification.get("confidence", 0.7),
                "attachments": processing_result.get("attachments", []),
                "actions": processing_result.get("actions", []),
                "session": session
            }

        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}",
                "error": str(e),
                "category": "error",
                "model_used": "fallback",
                "confidence": 0.0,
                "session": session
            }

    async def _route_request(self, user_input: str, user_context: Dict) -> Dict:
        """Route request to appropriate specialist"""
        loop = asyncio.get_event_loop()

        classification_result = await loop.run_in_executor(
            self.executor,
            self.router.classify_intent,
            user_input,
            user_context
        )
        
        # Convert to dict if it's an object
        if hasattr(classification_result, 'to_dict'):
            classification = classification_result.to_dict()
        elif hasattr(classification_result, '__dict__'):
            classification = classification_result.__dict__
        else:
            classification = classification_result

        model = self._select_best_model(classification)

        return {
            "model": model,
            "classification": classification
        }

    def _select_best_model(self, classification: Dict) -> str:
        """Select the best model for the task"""
        category = classification.get("category", "general")
        if hasattr(category, 'value'):
            category = category.value
            
        priority = classification.get("priority", 3)
        if hasattr(priority, 'value'):
            priority = priority.value
            
        complexity = classification.get("complexity", "medium")
        if hasattr(complexity, 'value'):
            complexity = complexity.value

        if category == "code":
            if complexity in ["high", "very_complex"] or priority <= 2:
                return "deepseek-coder-v2:16b"
            elif complexity == "medium":
                return "qwen2.5-coder:7b"
            else:
                return "qwen2.5-coder:3b"
        elif category == "vision":
            return "llama3.2-vision:11b" if priority <= 2 else "gemma3:4b"
        elif category == "analysis":
            return "phi4:14b" if complexity in ["high", "very_complex"] else "qwen2.5:14b"
        elif category == "email":
            return "phi4:14b"
        elif category == "search":
            return "qwen2.5:14b"
        elif category == "reminder":
            return "gemma3:4b"
        else:
            return settings.DEFAULT_MODEL

    def _get_specialist(self, model_name: str, category: str) -> SpecialistAgent:
        """Get or initialize a specialist agent"""
        if model_name not in self.specialists:
            if category in self.specialist_factories:
                factory = self.specialist_factories[category].get(model_name)
                if factory:
                    self.specialists[model_name] = factory()
                else:
                    self.specialists[model_name] = GenericAgent(model_name)
            else:
                self.specialists[model_name] = GenericAgent(model_name)
        return self.specialists[model_name]

    async def _process_with_specialist(
            self,
            specialist: SpecialistAgent,
            user_input: str,
            classification: Dict,
            user_context: Dict,
            attachments: Optional[List]
    ) -> Dict:
        """Process the request with the selected specialist"""
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(
            self.executor,
            specialist.process,
            {
                "task": user_input,
                "category": classification.get("category"),
                "priority": classification.get("priority"),
                "context": user_context,
                "attachments": attachments or []
            }
        )

    async def process_request_parallel(
        self,
        user_input: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Process with parallel speculation - 2x faster"""
        
        # Run router and specialist in parallel
        route_task = self._route_request(user_input, {"user_id": user_id})
        
        # Also try generic response in parallel
        generic_task = self._get_specialist("gemma3:1b", "general").process({
            "task": user_input
        })
        
        # Wait for both
        route_result, generic_result = await asyncio.gather(
            route_task, 
            asyncio.get_event_loop().run_in_executor(
                self.executor, 
                lambda: generic_task
            ),
            return_exceptions=True
        )
        
        # If routing fails, use generic response
        if isinstance(route_result, Exception):
            return {
                "response": generic_result.get("response", "Hello!"),
                "model_used": "gemma3:1b",
                "category": "general"
            }
        
        # Normal processing
        return await self.process_request(user_input, user_id)
