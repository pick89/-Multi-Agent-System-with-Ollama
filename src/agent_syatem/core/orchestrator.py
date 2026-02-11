import asyncio
import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from agent_system.config import settings
from agent_system.core.router_agent import RouterAgent
from agent_system.core.specialist_base import SpecialistAgent
from agent_system.agents.code_specialist import CodeSpecialist
from agent_system.agents.email_agent import EmailAgent
from agent_system.agents.vision_agent import VisionAgent
from agent_system.agents.analysis_agent import AnalysisAgent
from agent_system.memory.manager import MemoryManager
from agent_system.utils.logger import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Main orchestrator for the multi-agent system"""

    def __init__(self):
        self.router = RouterAgent()
        self.memory = MemoryManager()
        self.specialists: Dict[str, SpecialistAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=settings.WORKER_COUNT)

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

        # Get or create session
        session = session or {}

        # Load user context from memory
        user_context = await self.memory.get_user_context(user_id)

        try:
            # Step 1: Route the request
            route_result = await self._route_request(user_input, user_context)
            specialist_model = route_result["model"]
            classification = route_result["classification"]

            # Check if we need clarification
            if classification.get("requires_clarification"):
                return {
                    "requires_clarification": True,
                    "question": self._generate_clarification_question(classification),
                    "session": {"pending_intent": classification, **session}
                }

            # Step 2: Get or initialize specialist
            specialist = self._get_specialist(specialist_model, classification["category"])

            # Step 3: Process with specialist
            processing_result = await self._process_with_specialist(
                specialist,
                user_input,
                classification,
                user_context,
                attachments
            )

            # Step 4: Store in memory
            await self._store_interaction(
                user_id,
                user_input,
                processing_result,
                classification
            )

            # Step 5: Synthesize response
            final_response = await self._synthesize_response(
                user_input,
                processing_result,
                classification,
                user_context
            )

            return {
                "response": final_response,
                "model_used": specialist_model,
                "classification": classification,
                "attachments": processing_result.get("attachments", []),
                "actions": processing_result.get("actions", []),
                "session": session
            }

        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "error": str(e),
                "session": session
            }

    async def _route_request(self, user_input: str, user_context: Dict) -> Dict:
        """Route request to appropriate specialist"""
        loop = asyncio.get_event_loop()

        classification = await loop.run_in_executor(
            self.executor,
            self.router.classify_intent,
            user_input,
            user_context
        )

        # Determine best model based on task and user preferences
        model = self._select_best_model(classification)

        return {
            "model": model,
            "classification": classification
        }

    def _select_best_model(self, classification: Dict) -> str:
        """Select the best model for the task"""
        category = classification.get("category", "general")
        priority = classification.get("priority", 3)
        complexity = classification.get("complexity", "medium")

        if category == "code":
            if complexity == "high" or priority <= 2:
                return "deepseek-coder-v2:16b"
            elif complexity == "medium":
                return "qwen2.5-coder:7b"
            else:
                return "qwen2.5-coder:3b"

        elif category == "vision":
            if priority <= 2:
                return "llama3.2-vision:11b"
            else:
                return "gemma3:4b"

        elif category == "analysis":
            if complexity == "high":
                return "phi4:14b"
            else:
                return "qwen2.5:14b"

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
                    self.specialists[model_name] = SpecialistAgent(model_name)
            else:
                self.specialists[model_name] = SpecialistAgent(model_name)

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

    async def _synthesize_response(
            self,
            user_input: str,
            specialist_output: Dict,
            classification: Dict,
            user_context: Dict
    ) -> str:
        """Synthesize a final response from specialist output"""

        # Use aya:8b for multilingual synthesis if available
        if "aya:8b" in self.specialists:
            synthesizer = self.specialists["aya:8b"]
        else:
            synthesizer = self._get_specialist("gemma3:4b", "general")

        system_prompt = """You are a response synthesizer. Format the specialist's output into a clear, helpful response. 
        Use markdown for formatting. Be concise but complete. Adapt to the user's language."""

        prompt = f"""
        Original request: {user_input}

        Specialist output: {specialist_output}

        Task category: {classification.get('category')}
        Priority: {classification.get('priority')}

        Generate a well-formatted response:
        """

        return synthesizer.generate(prompt, system_prompt, temperature=0.3)

    async def _store_interaction(
            self,
            user_id: str,
            user_input: str,
            result: Dict,
            classification: Dict
    ):
        """Store interaction in memory"""
        await self.memory.add_interaction(
            user_id=user_id,
            user_input=user_input,
            system_response=result.get("response", ""),
            metadata={
                "category": classification.get("category"),
                "model_used": result.get("model_used"),
                "priority": classification.get("priority")
            }
        )

    def _generate_clarification_question(self, classification: Dict) -> str:
        """Generate a clarification question"""
        category = classification.get("category", "general")

        questions = {
            "code": "I need more details about the code you want. What programming language? What should it do?",
            "vision": "What image would you like me to analyze? Please upload it.",
            "email": "Which emails should I check? Any specific sender or subject?",
            "search": "What would you like me to search for?",
            "general": "Could you provide more details about what you need?"
        }

        return questions.get(category, "Could you please provide more details?")