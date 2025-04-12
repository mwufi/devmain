from typing import Dict, List, Optional
from .base_agent import BaseAgent
from .helper_creator import HelperCreator
from .evaluator_agent import EvaluatorAgent
from .infer_agent import InferAgent
import os
import json
from agents import Runner

class MasterAgent(BaseAgent):
    def __init__(self, name: str):
        instructions = """
        You are a great planner. You coordinate tasks and delegate to specialized agents.
        Your role is to:
        1. Understand user goals
        2. Break down tasks into subtasks
        3. Delegate to appropriate helper agents
        4. Evaluate results
        5. Consult with colleagues when needed
        """
        super().__init__(name, "MasterAgent", instructions)
        self.subtasks: List[Dict] = []
        self.colleagues: List[str] = ["Aria", "Bill"]
        self.helper_creator = HelperCreator()
        self.evaluator = EvaluatorAgent()
        self.infer_agent = InferAgent()
        self._load_bot_context()
        
    def _load_bot_context(self):
        """Load context from bot-context directory"""
        context_dir = "bot-context"
        if not os.path.exists(context_dir):
            os.makedirs(context_dir)
            
        for filename in os.listdir(context_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(context_dir, filename), "r") as f:
                    section_name = filename[:-4]  # Remove .txt extension
                    self.context[section_name] = f.read()
                    
    async def think(self, topic: str) -> Dict:
        """Think about a topic and return insights"""
        await self.log_event("think", {"topic": topic})
        result = await Runner.run(self, input=f"Think about: {topic}")
        return {"insights": result.final_output}
        
    async def infer_user_goals(self, user_input: str) -> Dict:
        """Infer user goals from input"""
        await self.log_event("infer_goals", {"input": user_input})
        result = await Runner.run(self.infer_agent, input=user_input)
        return result.final_output
        
    async def make_progress(self, task_id: str) -> Dict:
        """Make progress on a task"""
        await self.log_event("make_progress", {"task_id": task_id})
        result = await Runner.run(self, input=f"Make progress on task: {task_id}")
        return {"status": "progress_made", "details": result.final_output}
        
    async def set_subtask(self, task: Dict):
        """Set a new subtask"""
        self.subtasks.append(task)
        await self.log_event("set_subtask", {"task": task})
        
    async def mark_task_as_done(self, task_id: str):
        """Mark a task as completed"""
        await self.log_event("mark_task_done", {"task_id": task_id})
        self.subtasks = [t for t in self.subtasks if t["id"] != task_id]
        
    async def summon_execution_helper(self, task_description: str) -> Dict:
        """Summon a helper agent to execute a task"""
        await self.log_event("summon_helper", {"task": task_description})
        result = await Runner.run(self.helper_creator, input=task_description)
        return result.final_output
        
    async def evaluate_helper_results(self, results: Dict) -> Dict:
        """Evaluate results from a helper agent"""
        await self.log_event("evaluate_results", {"results": results})
        result = await Runner.run(self.evaluator, input=json.dumps(results))
        return result.final_output
        
    def list_colleagues(self) -> List[str]:
        """List available colleagues"""
        return self.colleagues
        
    async def consult_colleague(self, colleague: str, topic: str) -> Dict:
        """Consult a colleague about a topic"""
        if colleague not in self.colleagues:
            return {"error": f"Colleague {colleague} not found"}
            
        await self.log_event("consult_colleague", {
            "colleague": colleague,
            "topic": topic
        })
        
        # Create a temporary colleague agent
        colleague_agent = BaseAgent(
            name=colleague,
            role="Colleague",
            instructions=f"You are {colleague}, a knowledgeable colleague. Provide insights about {topic}."
        )
        
        result = await Runner.run(colleague_agent, input=topic)
        return {"response": result.final_output} 