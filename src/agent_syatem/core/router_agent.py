"""
Router Agent - Intent Classification and Model Selection
Uses gemma3:1b for ultra-fast routing (<100ms latency)

This agent is the entry point for all requests. It:
1. Classifies user intent into categories
2. Detects priority and urgency
3. Selects the optimal specialist model
4. Identifies missing information
5. Extracts entities and parameters
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

import ollama
from agent_system.config import settings
from agent_system.utils.logger import get_logger
from agent_system.utils.helpers import extract_code_blocks, detect_language
from agent_system.models.schemas import RouterClassification, Entity

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
            "entities": [e.dict() for e in self.entities],
            "suggested_questions": self.suggested_questions,
            "processing_time_ms": self.processing_time_ms,
            "fallback_used": self.fallback_used
        }


class RouterAgent:
    """
    Ultra-fast routing agent using gemma3:1b

    Capabilities:
    - Intent classification (50-100ms)
    - Priority detection
    - Entity extraction
    - Model selection
    - Clarification generation

    The router is designed to be:
    - FAST: Uses smallest model (1B parameters)
    - ACCURATE: Fine-tuned prompts with few-shot examples
    - RELIABLE: Fallback mechanisms for every step
    """

    def __init__(self, model_name: str = "gemma3:1b"):
        self.model = model_name
        self.fallback_model = "gemma3:1b"  # Same model, different prompt

        # Priority keywords with weights
        self.priority_keywords = {
            # URGENT (1)
            "urgent": PriorityLevel.URGENT,
            "asap": PriorityLevel.URGENT,
            "immediately": PriorityLevel.URGENT,
            "critical": PriorityLevel.URGENT,
            "emergency": PriorityLevel.URGENT,
            "deadline": PriorityLevel.URGENT,
            "as soon as possible": PriorityLevel.URGENT,
            "right now": PriorityLevel.URGENT,

            # HIGH (2)
            "high priority": PriorityLevel.HIGH,
            "important": PriorityLevel.HIGH,
            "quick": PriorityLevel.HIGH,
            "fast": PriorityLevel.HIGH,

            # NORMAL (3) - default
            "normal": PriorityLevel.NORMAL,
            "regular": PriorityLevel.NORMAL,

            # LOW (4)
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

        # Cache for frequently used patterns
        self._pattern_cache = {}

        logger.info(f"Router Agent initialized with model: {self.model}")

    def classify_intent(
            self,
            user_input: str,
            user_context: Optional[Dict] = None,
            timeout: int = 5
    ) -> RoutingDecision:
        """
        Main entry point - Classify user intent and make routing decision

        Args:
            user_input: Raw user message
            user_context: User preferences, history, etc.
            timeout: Maximum processing time in seconds

        Returns:
            Complete routing decision
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

            # Validate and fill missing fields
            decision = self._validate_decision(decision, user_input)

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
            # Ultimate fallback - safe default
            return self._get_safe_fallback(user_input)

    def _classify_with_llm(
            self,
            user_input: str,
            user_context: Optional[Dict] = None
    ) -> RoutingDecision:
        """Use LLM for intelligent classification"""

        # Build context string
        context_str = ""
        if user_context:
            context_str = f"""
            User Context:
            - Preferred language: {user_context.get('preferred_language', 'unknown')}
            - Previous category: {user_context.get('last_category', 'none')}
            - Expertise level: {user_context.get('expertise', 'beginner')}
            """

        # Create few-shot examples for better accuracy
        examples = self._get_few_shot_examples()

        prompt = f"""You are an intelligent router agent. Classify this user request and output ONLY valid JSON.

{examples}

User Input: "{user_input}"
{context_str}

Analyze and return JSON with these EXACT fields:
{{
    "category": "one of [code, vision, email, search, reminder, analysis, general, unknown]",
    "priority": 1-4 (1=urgent, 2=high, 3=normal, 4=low),
    "complexity": "simple/medium/complex/very_complex",
    "confidence": 0.0-1.0,
    "requires_clarification": true/false,
    "missing_fields": ["field1", "field2"],
    "entities": [
        {{"type": "language", "value": "python"}},
        {{"type": "time", "value": "3pm"}},
        {{"type": "email", "value": "user@example.com"}}
    ],
    "suggested_questions": ["question1", "question2"]
}}

Consider:
1. If input is vague, set requires_clarification=true and suggest questions
2. Extract entities like programming languages, times, emails, names
3. Set priority based on urgency keywords
4. Set complexity based on task difficulty

JSON:"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                format="json",
                options={
                    "temperature": 0.1,  # Low temperature for consistency
                    "num_predict": 512,
                    "top_k": 10,
                    "top_p": 0.5
                }
            )

            result = json.loads(response['response'])

            # Parse and validate
            category = IntentCategory(result.get("category", "unknown"))
            priority = PriorityLevel(result.get("priority", 3))
            complexity = ComplexityLevel(result.get("complexity", "medium"))

            # Select specialist model
            specialist_model = self._select_specialist_model(
                category,
                priority,
                complexity,
                result.get("entities", [])
            )

            # Create entities
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
                suggested_questions=result.get("suggested_questions", [])
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response.get('response', '')}")
            return self._rule_based_classification(user_input)

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self._rule_based_classification(user_input)

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

        # If no matches, default to general
        if category == IntentCategory.UNKNOWN:
            category = IntentCategory.GENERAL

        # Detect priority
        priority = PriorityLevel.NORMAL
        for keyword, level in self.priority_keywords.items():
            if keyword in user_input_lower:
                priority = level
                break

        # Detect complexity based on length and structure
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

        # Generate missing fields and questions
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
            confidence=0.6,  # Lower confidence for rule-based
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
        """Select the optimal specialist model based on routing decision"""

        # Get selection function for category
        selector = self.model_selection_rules.get(
            category,
            self._select_general_model
        )

        return selector(priority, complexity, entities)

    def _select_code_model(
            self,
            priority: PriorityLevel,
            complexity: ComplexityLevel,
            entities: List[Entity]
    ) -> str:
        """Select best code model based on requirements"""

        # Extract language if present
        language = None
        for entity in entities:
            if entity.type == "language":
                language = entity.value.lower()
                break

        # High priority or complex tasks use better models
        if priority <= PriorityLevel.HIGH or complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
            if settings.MODEL_CAPABILITIES.get("deepseek-coder-v2:16b"):
                return "deepseek-coder-v2:16b"
            return "qwen2.5-coder:7b"

        # Fast tasks use smaller model
        if priority == PriorityLevel.NORMAL and complexity == ComplexityLevel.SIMPLE:
            return "qwen2.5-coder:3b"

        # Default balanced choice
        return "qwen2.5-coder:7b"

    def _select_vision_model(
            self,
            priority: PriorityLevel,
            complexity: ComplexityLevel,
            entities: List[Entity]
    ) -> str:
        """Select best vision model"""

        if priority <= PriorityLevel.HIGH:
            return "llama3.2-vision:11b"

        # Check if OCR is needed
        for entity in entities:
            if entity.type == "task" and "ocr" in entity.value.lower():
                return "minicpm-v:8b"

        return "gemma3:4b"

    def _select_email_model(
            self,
            priority: PriorityLevel,
            complexity: ComplexityLevel,
            entities: List[Entity]
    ) -> str:
        """Email tasks always use phi4 for reliability"""
        return "phi4:14b"

    def _select_search_model(
            self,
            priority: PriorityLevel,
            complexity: ComplexityLevel,
            entities: List[Entity]
    ) -> str:
        """Search tasks use qwen2.5"""
        return "qwen2.5:14b"

    def _select_reminder_model(
            self,
            priority: PriorityLevel,
            complexity: ComplexityLevel,
            entities: List[Entity]
    ) -> str:
        """Reminders are simple, use small model"""
        return "gemma3:4b"

    def _select_analysis_model(
            self,
            priority: PriorityLevel,
            complexity: ComplexityLevel,
            entities: List[Entity]
    ) -> str:
        """Deep analysis needs powerful model"""
        if complexity == ComplexityLevel.VERY_COMPLEX:
            if settings.MODEL_CAPABILITIES.get("phi4:14b"):
                return "phi4:14b"
        return "qwen2.5:14b"

    def _select_general_model(
            self,
            priority: PriorityLevel,
            complexity: ComplexityLevel,
            entities: List[Entity]
    ) -> str:
        """General tasks use balanced model"""
        return settings.DEFAULT_MODEL

    def _detect_complexity(self, user_input: str) -> ComplexityLevel:
        """Detect task complexity based on input"""
        word_count = len(user_input.split())

        # Very short queries are simple
        if word_count < 5:
            return ComplexityLevel.SIMPLE

        # Check for complexity indicators
        complex_indicators = [
            "complex", "difficult", "advanced", "sophisticated",
            "architecture", "design pattern", "optimization",
            "multiple files", "integration", "distributed"
        ]

        very_complex_indicators = [
            "machine learning", "neural network", "deep learning",
            "enterprise", "production", "scalable", "high performance",
            "distributed system", "microservices", "kubernetes"
        ]

        input_lower = user_input.lower()

        for indicator in very_complex_indicators:
            if indicator in input_lower:
                return ComplexityLevel.VERY_COMPLEX

        for indicator in complex_indicators:
            if indicator in input_lower:
                return ComplexityLevel.COMPLEX

        # Medium complexity by default
        if word_count > 20:
            return ComplexityLevel.MEDIUM

        return ComplexityLevel.SIMPLE

    def _extract_entities_rule_based(self, user_input: str) -> List[Entity]:
        """Extract entities using regex patterns"""
        entities = []

        # Extract programming languages
        languages = [
            "python", "javascript", "typescript", "java", "go", "rust",
            "c\\+\\+", "c#", "php", "ruby", "swift", "kotlin"
        ]

        for lang in languages:
            pattern = r'\b' + lang + r'\b'
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

        # Extract times
        time_patterns = [
            r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?\b',
            r'\b(\d{1,2})\s*(am|pm|AM|PM)\b'
        ]

        for pattern in time_patterns:
            times = re.findall(pattern, user_input)
            for time_match in times:
                time_str = ''.join(time_match)
                if time_str:
                    entities.append(Entity(
                        type="time",
                        value=time_str.strip(),
                        confidence=0.8
                    ))

        return entities

    def _needs_clarification(
            self,
            category: IntentCategory,
            user_input: str,
            entities: List[Entity]
    ) -> bool:
        """Determine if clarification is needed"""

        # Check if input is too short
        if len(user_input.split()) < 3:
            return True

        # Check if required fields are missing
        required = self.required_fields.get(category, [])

        for field in required:
            if field == "language":
                has_language = any(e.type == "language" for e in entities)
                if not has_language and category == IntentCategory.CODE:
                    return True

            elif field == "query" and category == IntentCategory.SEARCH:
                # Check if there's actual search content
                query_terms = user_input.replace("search", "").replace("find", "").strip()
                if len(query_terms) < 3:
                    return True

            elif field == "time" and category == IntentCategory.REMINDER:
                has_time = any(e.type == "time" for e in entities)
                if not has_time:
                    return True

        return False

    def _get_missing_fields(
            self,
            category: IntentCategory,
            user_input: str,
            entities: List[Entity]
    ) -> List[str]:
        """Identify which required fields are missing"""
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
            elif field == "task_description" and category == IntentCategory.CODE:
                if len(user_input.split()) < 5:
                    missing.append("detailed task description")

        return missing

    def _generate_clarification_questions(
            self,
            category: IntentCategory,
            missing_fields: List[str]
    ) -> List[str]:
        """Generate intelligent clarification questions"""
        questions = []

        question_templates = {
            IntentCategory.CODE: {
                "programming language": "What programming language would you like me to use?",
                "detailed task description": "Could you describe in more detail what the code should do?",
                "default": "What specific code functionality do you need?"
            },
            IntentCategory.VISION: {
                "image_source": "Please upload the image you'd like me to analyze.",
                "default": "What would you like me to analyze in the image?"
            },
            IntentCategory.EMAIL: {
                "action": "Would you like to check, reply to, or compose an email?",
                "default": "What would you like me to do with your emails?"
            },
            IntentCategory.SEARCH: {
                "search query": "What would you like me to search for?",
                "default": "What information are you looking for?"
            },
            IntentCategory.REMINDER: {
                "time": "When would you like me to remind you?",
                "message": "What should I remind you about?",
                "default": "What reminder would you like to set?"
            },
            IntentCategory.ANALYSIS: {
                "subject": "What would you like me to analyze?",
                "default": "What do you need help analyzing?"
            }
        }

        templates = question_templates.get(category, {})

        for field in missing_fields:
            if field in templates:
                questions.append(templates[field])

        # Add default question if no specific ones
        if not questions:
            questions.append(templates.get("default", "Could you provide more details?"))

        return questions[:3]  # Max 3 questions

    def _validate_decision(
            self,
            decision: RoutingDecision,
            user_input: str
    ) -> RoutingDecision:
        """Validate and fix routing decision"""

        # Ensure category is valid
        if not isinstance(decision.category, IntentCategory):
            decision.category = IntentCategory.GENERAL

        # Ensure priority is valid
        if not isinstance(decision.priority, PriorityLevel):
            decision.priority = PriorityLevel.NORMAL

        # Ensure confidence is within bounds
        decision.confidence = max(0.0, min(1.0, decision.confidence))

        # Check if model exists, otherwise use default
        if decision.specialist_model not in settings.MODEL_CAPABILITIES:
            logger.warning(f"Model {decision.specialist_model} not available, using default")
            decision.specialist_model = settings.DEFAULT_MODEL
            decision.fallback_used = True

        return decision

    def _get_safe_fallback(self, user_input: str) -> RoutingDecision:
        """Ultimate fallback when everything fails"""
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

    def _get_few_shot_examples(self) -> str:
        """Get few-shot examples for LLM"""
        return """
        EXAMPLES:

        Input: "Write a Python function to calculate fibonacci"
        Output: {
            "category": "code",
            "priority": 3,
            "complexity": "medium",
            "confidence": 0.95,
            "requires_clarification": false,
            "missing_fields": [],
            "entities": [{"type": "language", "value": "python"}],
            "suggested_questions": []
        }

        Input: "Check my email for messages from John"
        Output: {
            "category": "email",
            "priority": 2,
            "complexity": "simple",
            "confidence": 0.9,
            "requires_clarification": false,
            "missing_fields": [],
            "entities": [{"type": "name", "value": "John"}],
            "suggested_questions": []
        }

        Input: "Search"
        Output: {
            "category": "search",
            "priority": 3,
            "complexity": "simple",
            "confidence": 0.6,
            "requires_clarification": true,
            "missing_fields": ["search query"],
            "entities": [],
            "suggested_questions": ["What would you like me to search for?"]
        }

        Input: "Remind me tomorrow"
        Output: {
            "category": "reminder",
            "priority": 3,
            "complexity": "simple",
            "confidence": 0.7,
            "requires_clarification": true,
            "missing_fields": ["time", "message"],
            "entities": [],
            "suggested_questions": [
                "What time tomorrow?",
                "What should I remind you about?"
            ]
        }
        """

    def get_routing_stats(self) -> Dict:
        """Get router performance statistics"""
        return {
            "model": self.model,
            "capabilities": list(self.category_keywords.keys()),
            "priority_levels": [p.value for p in PriorityLevel],
            "default_fallback": settings.DEFAULT_MODEL,
            "total_categories": len(IntentCategory)
        }


# Singleton instance for global use
_router_instance: Optional[RouterAgent] = None


def get_router() -> RouterAgent:
    """Get or create router singleton"""
    global _router_instance
    if _router_instance is None:
        _router_instance = RouterAgent()
    return _router_instance