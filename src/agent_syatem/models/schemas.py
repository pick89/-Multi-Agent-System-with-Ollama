"""
Pydantic schemas for data validation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class Entity(BaseModel):
    """Extracted entity from user input"""
    type: str = Field(..., description="Entity type (language, time, email, etc)")
    value: str = Field(..., description="Entity value")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Extraction confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "language",
                "value": "python",
                "confidence": 0.95,
                "metadata": {"version": "3.11"}
            }
        }


class RouterClassification(BaseModel):
    """Complete router classification output"""
    category: str = Field(..., description="Intent category")
    priority: int = Field(3, ge=1, le=4, description="Priority level (1-4)")
    complexity: str = Field("medium", description="Task complexity")
    specialist_model: str = Field(..., description="Selected model")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    requires_clarification: bool = Field(False, description="Whether clarification is needed")
    missing_fields: List[str] = Field(default_factory=list, description="Missing required fields")
    entities: List[Entity] = Field(default_factory=list, description="Extracted entities")
    suggested_questions: List[str] = Field(default_factory=list, description="Clarification questions")
    processing_time_ms: float = Field(0.0, description="Processing time in milliseconds")
    fallback_used: bool = Field(False, description="Whether fallback was used")

    @validator('category')
    def validate_category(cls, v):
        valid_categories = [
            'code', 'vision', 'email', 'search',
            'reminder', 'analysis', 'general', 'unknown'
        ]
        if v not in valid_categories:
            return 'unknown'
        return v

    @validator('priority')
    def validate_priority(cls, v):
        if v < 1:
            return 1
        if v > 4:
            return 4
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "category": "code",
                "priority": 3,
                "complexity": "medium",
                "specialist_model": "qwen2.5-coder:7b",
                "confidence": 0.95,
                "requires_clarification": False,
                "missing_fields": [],
                "entities": [
                    {
                        "type": "language",
                        "value": "python",
                        "confidence": 0.95
                    }
                ],
                "suggested_questions": [],
                "processing_time_ms": 85.3,
                "fallback_used": False
            }
        }