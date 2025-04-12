from .base_agent import BaseAgent
from typing import Dict, List
from agents import Runner

class InferAgent(BaseAgent):
    def __init__(self):
        instructions = """
        You are an InferAgent specialized in understanding user goals and intentions.
        Your role is to:
        1. Extract explicit and implicit goals from user input
        2. Categorize goals into different types
        3. Prioritize goals based on urgency and importance
        4. Provide confidence scores for your inferences
        """
        super().__init__("InferAgent", "Goal Inference", instructions)
        
    async def process(self, user_input: str) -> Dict:
        """Process user input to infer goals"""
        await self.log_event("infer_goals", {"input": user_input})
        
        # Get goal inference from the agent
        result = await Runner.run(self, input=f"Infer goals from: {user_input}")
        
        # Extract goals from the response
        goals = await self._extract_goals(result.final_output)
        
        # Categorize goals
        categorized_goals = await self._categorize_goals(goals)
        
        # Determine priority
        prioritized_goals = await self._prioritize_goals(categorized_goals)
        
        return {
            "raw_goals": goals,
            "categorized_goals": categorized_goals,
            "prioritized_goals": prioritized_goals,
            "confidence_score": await self._calculate_confidence(goals),
            "agent_analysis": result.final_output
        }
        
    async def _extract_goals(self, text: str) -> List[str]:
        """Extract potential goals from text"""
        result = await Runner.run(self, input=f"Extract goals from: {text}")
        response = result.final_output
        
        # Split response into goals
        goals = [g.strip() for g in response.split('\n') if g.strip()]
        return goals
        
    async def _categorize_goals(self, goals: List[str]) -> Dict[str, List[str]]:
        """Categorize goals into different types"""
        result = await Runner.run(self, input=f"Categorize these goals: {goals}")
        response = result.final_output
        
        categories = {
            "information": [],
            "action": [],
            "learning": [],
            "creation": [],
            "other": []
        }
        
        # Parse the response to categorize goals
        for goal in goals:
            category_result = await Runner.run(self, input=f"Categorize this goal: {goal}")
            category = category_result.final_output.lower()
            
            if "information" in category:
                categories["information"].append(goal)
            elif "action" in category:
                categories["action"].append(goal)
            elif "learning" in category:
                categories["learning"].append(goal)
            elif "creation" in category:
                categories["creation"].append(goal)
            else:
                categories["other"].append(goal)
                
        return categories
        
    async def _prioritize_goals(self, categorized_goals: Dict[str, List[str]]) -> List[Dict]:
        """Prioritize goals based on category and content"""
        priorities = []
        
        # Define category priorities
        category_priority = {
            "action": 1.0,
            "creation": 0.9,
            "learning": 0.8,
            "information": 0.7,
            "other": 0.5
        }
        
        for category, goals in categorized_goals.items():
            for goal in goals:
                # Get priority from the agent
                result = await Runner.run(self, input=f"Prioritize this goal: {goal}")
                response = result.final_output.lower()
                
                # Calculate urgency based on response
                urgency = 0.5  # Base urgency
                if "urgent" in response or "immediately" in response:
                    urgency += 0.3
                if "important" in response or "critical" in response:
                    urgency += 0.2
                    
                priority = category_priority[category] * urgency
                
                priorities.append({
                    "goal": goal,
                    "category": category,
                    "priority": priority,
                    "agent_analysis": response
                })
                
        # Sort by priority
        return sorted(priorities, key=lambda x: x["priority"], reverse=True)
        
    async def _calculate_confidence(self, goals: List[str]) -> float:
        """Calculate confidence in goal inference"""
        if not goals:
            return 0.0
            
        # Get confidence assessment from the agent
        result = await Runner.run(self, input=f"Assess confidence in these goals: {goals}")
        response = result.final_output.lower()
        
        confidence = 0.5  # Base confidence
        
        # Adjust confidence based on response
        if "high confidence" in response or "certain" in response:
            confidence += 0.3
        if "clear" in response or "explicit" in response:
            confidence += 0.2
            
        return min(1.0, confidence) 