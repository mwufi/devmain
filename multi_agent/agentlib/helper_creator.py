from .base_agent import BaseAgent
from typing import Dict
from agents import Runner

class HelperCreator(BaseAgent):
    def __init__(self):
        instructions = """
        You are a Helper Creator agent. Your role is to:
        1. Analyze task descriptions
        2. Determine the appropriate type of helper needed
        3. Create specialized helper agents for specific tasks
        4. Define their capabilities and scope
        """
        super().__init__("HelperCreator", "Helper Creator", instructions)
        
    async def create_helper(self, task_description: str) -> Dict:
        """Create a helper agent for a specific task"""
        await self.log_event("create_helper", {"task": task_description})
        
        # Analyze the task description and create appropriate helper
        helper_type = await self._determine_helper_type(task_description)
        
        # Create a specialized helper agent
        helper_agent = BaseAgent(
            name=f"{helper_type}Helper",
            role="Specialized Helper",
            instructions=self._get_helper_instructions(helper_type, task_description)
        )
        
        # Run the helper agent to get its capabilities
        result = await Runner.run(helper_agent, input=task_description)
        
        return {
            "helper_type": helper_type,
            "task": task_description,
            "capabilities": self._get_helper_capabilities(helper_type),
            "response": result.final_output
        }
        
    async def _determine_helper_type(self, task_description: str) -> str:
        """Determine the type of helper needed based on task description"""
        result = await Runner.run(self, input=f"Analyze this task and determine the best helper type: {task_description}")
        response = result.final_output.lower()
        
        if "code" in response or "program" in response:
            return "CodeHelper"
        elif "research" in response or "find" in response:
            return "ResearchHelper"
        elif "analyze" in response or "evaluate" in response:
            return "AnalysisHelper"
        else:
            return "GeneralHelper"
            
    def _get_helper_capabilities(self, helper_type: str) -> Dict:
        """Get the capabilities of a specific helper type"""
        capabilities = {
            "CodeHelper": {
                "capabilities": ["write_code", "debug", "optimize"],
                "languages": ["Python", "JavaScript", "TypeScript"]
            },
            "ResearchHelper": {
                "capabilities": ["search", "summarize", "synthesize"],
                "sources": ["web", "documents", "databases"]
            },
            "AnalysisHelper": {
                "capabilities": ["analyze", "evaluate", "compare"],
                "methods": ["statistical", "qualitative", "quantitative"]
            },
            "GeneralHelper": {
                "capabilities": ["assist", "organize", "coordinate"],
                "domains": ["general", "administrative", "coordination"]
            }
        }
        
        return capabilities.get(helper_type, capabilities["GeneralHelper"])
        
    def _get_helper_instructions(self, helper_type: str, task: str) -> str:
        """Generate instructions for the helper agent"""
        base_instructions = {
            "CodeHelper": "You are a specialized coding assistant. Write clean, efficient code and provide explanations.",
            "ResearchHelper": "You are a research assistant. Find relevant information and provide well-structured summaries.",
            "AnalysisHelper": "You are an analysis expert. Evaluate data and provide insights with supporting evidence.",
            "GeneralHelper": "You are a general assistant. Help with various tasks and coordinate with other agents."
        }
        
        return f"{base_instructions.get(helper_type, base_instructions['GeneralHelper'])}\n\nCurrent task: {task}" 