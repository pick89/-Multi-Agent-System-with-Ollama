# ruff: noqa: F401, E402, ARG002
# pylint: disable=unused-import,unused-argument

#!/usr/bin/env python3
"""
Router Agent - Intent Classification and Model Selection
Uses gemma3:1b for ultra-fast routing (<100ms latency)
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from agent_system.utils.ollama_client import get_ollama_client  # noqa: F401
from agent_system.config import settings
from agent_system.utils.logger import get_logger  # noqa: F401
# from agent_system.utils.helpers import extract_code_blocks, detect_language  # Unused
from agent_system.models.schemas import RouterClassification, Entity, Entity  # noqa: F401, Entity

logger = get_logger(__name__)


class IntentCategory(str, Enum):
    """User intent categories"""
    CODE = "code"
    VISION = "vision"
    EMAIL = "email"
    SEARCH = "search"
    REMINDER = "reminder"
    ANALYSIS = "analysis"
    GENERAL = "general"
    UNKNOWN = "unknown"


class PriorityLevel(int, Enum):
    """Priority levels for task handling"""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class ComplexityLevel(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class RoutingDecision:
    """Complete routing decision data"""
    category: IntentCategory
    priority: PriorityLevel
    complexity: ComplexityLevel
    specialist_model: str
    confidence: float
    requires_clarification: bool
    missing_fields: List[str] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    suggested_questions: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    fallback_used: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "category": self.category.value,
            "priority": self.priority.value,
            "complexity": self.complexity.value,
            "specialist_model": self.specialist_model,
            "confidence": self.confidence,
            "requires_clarification": self.requires_clarification,
            "missing_fields": self.missing_fields,
            "entities": [e.dict() if hasattr(e, 'dict') else {'type': e.type, 'value': e.value} for e in self.entities],
            "suggested_questions": self.suggested_questions,
            "processing_time_ms": self.processing_time_ms,
            "fallback_used": self.fallback_used
        }


class RouterAgent:
    """
    Ultra-fast routing agent using gemma3:1b
    """
    
    def __init__(self, model_name: str = "gemma3:1b"):
        self.model = model_name
        self.client = get_ollama_client()
        self.fallback_model = "gemma3:1b"
        
        # Priority keywords with weights
        self.priority_keywords = {
            "urgent": PriorityLevel.URGENT,
            "asap": PriorityLevel.URGENT,
            "immediately": PriorityLevel.URGENT,
            "critical": PriorityLevel.URGENT,
            "emergency": PriorityLevel.URGENT,
            "deadline": PriorityLevel.URGENT,
            "as soon as possible": PriorityLevel.URGENT,
            "right now": PriorityLevel.URGENT,
            "high priority": PriorityLevel.HIGH,
            "important": PriorityLevel.HIGH,
            "quick": PriorityLevel.HIGH,
            "fast": PriorityLevel.HIGH,
            "normal": PriorityLevel.NORMAL,
            "regular": PriorityLevel.NORMAL,
            "low priority": PriorityLevel.LOW,
            "when you have time": PriorityLevel.LOW,
            "not urgent": PriorityLevel.LOW,
            "whenever": PriorityLevel.LOW
        }
        
        # Category keywords for fallback classification
        self.category_keywords = {
            IntentCategory.CODE: [
                "code", "program", "script", "function", "class", "method",
                "python", "javascript", "java", "go", "rust", "c++", "api",
                "algorithm", "debug", "compile", "execute", "run", "test",
                "write", "implement", "develop", "programming", "software"
            ],
            IntentCategory.VISION: [
                "image", "picture", "photo", "vision", "see", "look",
                "ocr", "extract text", "recognize", "detect", "identify",
                "visual", "camera", "scan", "document", "receipt", "face"
            ],
            IntentCategory.EMAIL: [
                "email", "mail", "inbox", "send", "reply", "forward",
                "outlook", "gmail", "message", "compose", "draft"
            ],
            IntentCategory.SEARCH: [
                "search", "find", "look up", "google", "internet",
                "web", "online", "research", "information about",
                "what is", "who is", "how to", "when did"
            ],
            IntentCategory.REMINDER: [
                "remind", "reminder", "alert", "notify", "notification",
                "schedule", "calendar", "appointment", "meeting",
                "remember", "don't forget", "todo", "task"
            ],
            IntentCategory.ANALYSIS: [
                "analyze", "analysis", "explain", "understand",
                "summarize", "summarise", "compare", "contrast",
                "evaluate", "assess", "review", "study", "examine",
                "reasoning", "logic", "math", "calculate", "compute"
            ]
        }
        
        # Model selection rules
        self.model_selection_rules = {
            IntentCategory.CODE: self._select_code_model,
            IntentCategory.VISION: self._select_vision_model,
            IntentCategory.EMAIL: self._select_email_model,
            IntentCategory.SEARCH: self._select_search_model,
            IntentCategory.REMINDER: self._select_reminder_model,
            IntentCategory.ANALYSIS: self._select_analysis_model,
            IntentCategory.GENERAL: self._select_general_model
        }
        
        # Fields required for each category
        self.required_fields = {
            IntentCategory.CODE: ["language", "task_description"],
            IntentCategory.VISION: ["image_source"],
            IntentCategory.EMAIL: ["action"],
            IntentCategory.SEARCH: ["query"],
            IntentCategory.REMINDER: ["time", "message"],
            IntentCategory.ANALYSIS: ["subject"],
            IntentCategory.GENERAL: ["query"]
        }
        
        logger.info(f"Router Agent initialized with model: {self.model}")
    
    def classify_intent(  # noqa: C901, ARG002
        self,
        user_input: str,
        user_context: Optional[Dict] = None,
        timeout: int = 5
    ) -> RoutingDecision:
        """
        Main entry point - Classify user intent and make routing decision
        """
        start_time = datetime.now()
        
        try:
            # Try primary classification with LLM
            decision = self._classify_with_llm(user_input, user_context)
            
            # If LLM fails or low confidence, use rule-based fallback
            if decision.confidence < 0.6:
                logger.warning(f"Low confidence ({decision.confidence}), using fallback")
                fallback_decision = self._rule_based_classification(user_input)
                fallback_decision.fallback_used = True
                decision = fallback_decision
            
            # Calculate processing time
            decision.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(
                f"Routing decision: {decision.category.value} | "
                f"Model: {decision.specialist_model} | "
                f"Confidence: {decision.confidence:.2f} | "
                f"Time: {decision.processing_time_ms:.0f}ms"
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in classify_intent: {e}", exc_info=True)
            return self._get_safe_fallback(user_input)
    
    
    def _rule_based_classification(self, user_input: str) -> RoutingDecision:
        """Fallback rule-based classification"""
        user_input_lower = user_input.lower()
        
        # Detect category by keywords
        category = IntentCategory.UNKNOWN
        max_matches = 0
        
        for cat, keywords in self.category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in user_input_lower)
            if matches > max_matches:
                max_matches = matches
                category = cat
        
        if category == IntentCategory.UNKNOWN:
            category = IntentCategory.GENERAL
        
        # Detect priority
        priority = PriorityLevel.NORMAL
        for keyword, level in self.priority_keywords.items():
            if keyword in user_input_lower:
                priority = level
                break
        
        # Detect complexity
        complexity = self._detect_complexity(user_input)
        
        # Extract entities
        entities = self._extract_entities_rule_based(user_input)
        
        # Select model
        specialist_model = self._select_specialist_model(
            category,
            priority,
            complexity,
            entities
        )
        
        # Determine if clarification is needed
        requires_clarification = self._needs_clarification(category, user_input, entities)
        
        missing_fields = []
        suggested_questions = []
        
        if requires_clarification:
            missing_fields = self._get_missing_fields(category, user_input, entities)
            suggested_questions = self._generate_clarification_questions(
                category,
                missing_fields
            )
        
        return RoutingDecision(
            category=category,
            priority=priority,
            complexity=complexity,
            specialist_model=specialist_model,
            confidence=0.6,
            requires_clarification=requires_clarification,
            missing_fields=missing_fields,
            entities=entities,
            suggested_questions=suggested_questions,
            fallback_used=True
        )
    
    def _select_specialist_model(
        self,
        category: IntentCategory,
        priority: PriorityLevel,
        complexity: ComplexityLevel,
        entities: List[Entity]
    ) -> str:
        """Select the optimal specialist model"""
        selector = self.model_selection_rules.get(
            category,
            self._select_general_model
        )
        return selector(priority, complexity, entities)
    
    def _select_code_model(self, priority: PriorityLevel, complexity: ComplexityLevel, entities: List[Entity]) -> str:
        if priority <= PriorityLevel.HIGH or complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
            return "deepseek-coder-v2:16b"
        elif complexity == ComplexityLevel.MEDIUM:
            return "qwen2.5-coder:7b"
        else:
            return "qwen2.5-coder:3b"
    
    def _select_vision_model(self, priority: PriorityLevel, complexity: ComplexityLevel, entities: List[Entity]) -> str:
        if priority <= PriorityLevel.HIGH:
            return "llama3.2-vision:11b"
        return "gemma3:4b"
    
    def _select_email_model(self, priority: PriorityLevel, complexity: ComplexityLevel, entities: List[Entity]) -> str:
        return "phi4:14b"
    
    def _select_search_model(self, priority: PriorityLevel, complexity: ComplexityLevel, entities: List[Entity]) -> str:
        return "qwen2.5:14b"
    
    def _select_reminder_model(self, priority: PriorityLevel, complexity: ComplexityLevel, entities: List[Entity]) -> str:
        return "gemma3:4b"
    
    def _select_analysis_model(self, priority: PriorityLevel, complexity: ComplexityLevel, entities: List[Entity]) -> str:
        if complexity == ComplexityLevel.VERY_COMPLEX:
            return "phi4:14b"
        return "qwen2.5:14b"
    
    def _select_general_model(self, priority: PriorityLevel, complexity: ComplexityLevel, entities: List[Entity]) -> str:
        return settings.DEFAULT_MODEL
    
    def _detect_complexity(self, user_input: str) -> ComplexityLevel:
        word_count = len(user_input.split())
        
        if word_count < 5:
            return ComplexityLevel.SIMPLE
        
        complex_indicators = [
            "complex", "difficult", "advanced", "sophisticated",
            "architecture", "design pattern", "optimization"
        ]
        
        very_complex_indicators = [
            "machine learning", "neural network", "deep learning",
            "enterprise", "production", "scalable", "distributed system"
        ]
        
        input_lower = user_input.lower()
        
        for indicator in very_complex_indicators:
            if indicator in input_lower:
                return ComplexityLevel.VERY_COMPLEX
        
        for indicator in complex_indicators:
            if indicator in input_lower:
                return ComplexityLevel.COMPLEX
        
        return ComplexityLevel.MEDIUM if word_count > 20 else ComplexityLevel.SIMPLE
    
    def _extract_entities_rule_based(self, user_input: str) -> List[Entity]:
        entities = []
        
        # Extract programming languages
        languages = [
            "python", "javascript", "typescript", "java", "go", "rust",
            "c\\+\\+", "c#", "php", "ruby", "swift", "kotlin"
        ]
        
        for lang in languages:
            pattern = r'\b' + lang.replace('\\', '') + r'\b'
            if re.search(pattern, user_input.lower()):
                entities.append(Entity(
                    type="language",
                    value=lang.replace('\\', ''),
                    confidence=0.9
                ))
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_input)
        for email in emails:
            entities.append(Entity(
                type="email",
                value=email,
                confidence=1.0
            ))
        
        return entities
    
    def _needs_clarification(self, category: IntentCategory, user_input: str, entities: List[Entity]) -> bool:
        if len(user_input.split()) < 3:
            return True
        
        required = self.required_fields.get(category, [])
        entity_types = [e.type for e in entities]
        
        for field in required:
            if field == "language" and "language" not in entity_types and category == IntentCategory.CODE:
                return True
            elif field == "time" and "time" not in entity_types and category == IntentCategory.REMINDER:
                return True
            elif field == "query" and category == IntentCategory.SEARCH:
                query = user_input.replace("search", "").replace("find", "").strip()
                if len(query) < 3:
                    return True
        
        return False
    
    def _get_missing_fields(self, category: IntentCategory, user_input: str, entities: List[Entity]) -> List[str]:
        missing = []
        required = self.required_fields.get(category, [])
        entity_types = [e.type for e in entities]
        
        for field in required:
            if field == "language" and "language" not in entity_types:
                missing.append("programming language")
            elif field == "time" and "time" not in entity_types:
                missing.append("time")
            elif field == "query" and category == IntentCategory.SEARCH:
                query = user_input.replace("search", "").replace("find", "").strip()
                if len(query) < 3:
                    missing.append("search query")
        
        return missing
    
    def _generate_clarification_questions(self, category: IntentCategory, missing_fields: List[str]) -> List[str]:
        questions = []
        
        templates = {
            IntentCategory.CODE: {
                "programming language": "What programming language would you like me to use?",
                "task_description": "Could you describe in more detail what the code should do?",
            },
            IntentCategory.VISION: {
                "image_source": "Please upload the image you'd like me to analyze.",
            },
            IntentCategory.EMAIL: {
                "action": "Would you like to check, reply to, or compose an email?",
            },
            IntentCategory.SEARCH: {
                "search query": "What would you like me to search for?",
            },
            IntentCategory.REMINDER: {
                "time": "When would you like me to remind you?",
                "message": "What should I remind you about?",
            }
        }
        
        cat_templates = templates.get(category, {})
        
        for field in missing_fields:
            if field in cat_templates:
                questions.append(cat_templates[field])
        
        if not questions:
            questions.append("Could you provide more details?")
        
        return questions[:3]
    
    def _get_safe_fallback(self, user_input: str) -> RoutingDecision:
        logger.error("Using ULTIMATE fallback router")
        return RoutingDecision(
            category=IntentCategory.GENERAL,
            priority=PriorityLevel.NORMAL,
            complexity=ComplexityLevel.MEDIUM,
            specialist_model=settings.DEFAULT_MODEL,
            confidence=0.3,
            requires_clarification=True,
            missing_fields=["query"],
            suggested_questions=["Could you please rephrase your request?"],
            fallback_used=True
        )
    def _get_safe_fallback(self, user_input: str) -> RoutingDecision:
        """Ultimate fallback when everything fails"""
        logger.warning("Using rule-based fallback (LLM unavailable)")
        return self._rule_based_classification(user_input)

    def _is_greeting(self, user_input: str) -> bool:
        """Detect if input is a greeting"""
        greetings = ['hello', 'hi', 'hey', 'greetings', 'howdy', 'hola', 
                    'good morning', 'good afternoon', 'good evening']
        return any(greeting in user_input.lower() for greeting in greetings)
    
    def _rule_based_classification(self, user_input: str) -> RoutingDecision:
        """Fallback rule-based classification - enhanced for greetings"""
        user_input_lower = user_input.lower()
        
        # Check for greetings first
        if self._is_greeting(user_input):
            return RoutingDecision(
                category=IntentCategory.GENERAL,
                priority=PriorityLevel.NORMAL,
                complexity=ComplexityLevel.SIMPLE,
                specialist_model="phi4:14b",
                confidence=0.95,
                requires_clarification=False,
                missing_fields=[],
                entities=[],
                suggested_questions=[],
                fallback_used=True
            )
        
        # Rest of existing rule-based classification...
        # [Keep all your existing code here]

    def _select_general_model(self, priority: PriorityLevel, complexity: ComplexityLevel, _entities: List[Entity]) -> str:
        """Select FAST model for general chat - 3x faster"""
        # Use gemma3:1b for chat - it's 10x faster than phi4:14b
        return "gemma3:1b"  # Changed from phi4:14b

    def _classify_with_llm(
        self,
        user_input: str,
        user_context: Optional[Dict] = None
    ) -> RoutingDecision:
        """Use LLM for intelligent classification - FIXED asyncio version"""
        
        import asyncio
        import json
        from agent_system.utils.ollama_client import get_ollama_client
        
        context_str = ""
        if user_context:
            context_str = f"""
            User Context:
            - Preferred language: {user_context.get('preferred_language', 'unknown')}
            - Previous category: {user_context.get('last_category', 'none')}
            - Expertise level: {user_context.get('expertise', 'beginner')}
            """
        
        messages = [
            {
                "role": "system",
                "content": """You are an intelligent router agent. Classify user intent and output ONLY valid JSON.
                Categories: code, vision, email, search, reminder, analysis, general, unknown
                Priority: 1=urgent, 2=high, 3=normal, 4=low
                Complexity: simple, medium, complex, very_complex"""
            },
            {
                "role": "user",
                "content": f"""
                User Input: "{user_input}"
                {context_str}
                
                Return JSON with:
                - category: string
                - priority: integer (1-4)
                - complexity: string
                - confidence: float (0-1)
                - requires_clarification: boolean
                - missing_fields: list
                - entities: list of {{"type": str, "value": str}}
                - suggested_questions: list
                """
            }
        ]
        
        try:
            # Create new event loop for this operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                client = get_ollama_client()
                response = loop.run_until_complete(
                    client.chat(
                        model=self.model,
                        messages=messages,
                        format="json",
                        options={"temperature": 0.1}
                    )
                )
                
                result = json.loads(response["message"]["content"])
                
                category = IntentCategory(result.get("category", "unknown"))
                priority = PriorityLevel(result.get("priority", 3))
                complexity = ComplexityLevel(result.get("complexity", "medium"))
                
                specialist_model = self._select_specialist_model(
                    category,
                    priority,
                    complexity,
                    result.get("entities", [])
                )
                
                entities = []
                for e in result.get("entities", []):
                    entities.append(Entity(
                        type=e.get("type", "unknown"),
                        value=e.get("value", ""),
                        confidence=e.get("confidence", 0.8)
                    ))
                
                return RoutingDecision(
                    category=category,
                    priority=priority,
                    complexity=complexity,
                    specialist_model=specialist_model,
                    confidence=float(result.get("confidence", 0.7)),
                    requires_clarification=bool(result.get("requires_clarification", False)),
                    missing_fields=result.get("missing_fields", []),
                    entities=entities,
                    suggested_questions=result.get("suggested_questions", []),
                    fallback_used=False
                )
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self._rule_based_classification(user_input)
