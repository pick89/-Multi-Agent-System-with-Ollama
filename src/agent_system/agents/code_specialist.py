"""
Code generation specialist agent
"""

from typing import Dict, Any, List
from agent_system.core.specialist_base import SpecialistAgent


class CodeSpecialist(SpecialistAgent):
    """Specialist agent for code generation"""
    
    def __init__(self, model_name: str = "qwen2.5-coder:7b"):
        super().__init__(model_name)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process code generation request"""
        task = input_data.get("task", "")
        
        # Check if this is actually a code request
        code_keywords = ['code', 'function', 'class', 'script', 'program', 
                        'write', 'implement', 'python', 'javascript', 'java']
        
        is_code_request = any(keyword in task.lower() for keyword in code_keywords)
        
        if not is_code_request:
            # This isn't really a code request - pass to generic handler
            return {
                "response": "I'm the code specialist. Did you want help with programming?",
                "model_used": self.model,
                "actions": []
            }
        
        system_prompt = """You are an expert programmer. Generate clean, efficient, well-documented code.
        Include example usage and error handling where appropriate.
        Respond with ONLY the code block, no additional text."""
        
        try:
            response = self.generate(task, system_prompt, temperature=0.3)
            
            # Detect language for syntax highlighting
            language = "python"
            if "javascript" in task.lower() or "js" in task.lower():
                language = "javascript"
            elif "java" in task.lower():
                language = "java"
            elif "go" in task.lower():
                language = "go"
            elif "rust" in task.lower():
                language = "rust"
            
            return {
                "response": f"Here's the code you requested:\n```{language}\n{response}\n```",
                "language": language,
                "code": response,
                "model_used": self.model,
                "actions": [
                    {"label": "📋 Copy Code", "callback_data": "copy_code"},
                    {"label": "▶️ Run Code", "callback_data": "run_code"}
                ]
            }
        except Exception as e:
            return {
                "response": "I encountered an error generating the code. Please try again with more specific requirements.",
                "model_used": self.model,
                "actions": []
            }
