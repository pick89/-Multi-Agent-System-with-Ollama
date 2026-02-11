"""Specialist agents for different tasks"""

from agent_system.agents.code_specialist import CodeSpecialist
from agent_system.agents.generic_agent import GenericAgent
from agent_system.agents.email_agent import EmailAgent
from agent_system.agents.vision_agent import VisionAgent
from agent_system.agents.analysis_agent import AnalysisAgent

__all__ = [
    "CodeSpecialist",
    "GenericAgent",
    "EmailAgent",
    "VisionAgent",
    "AnalysisAgent"
]
