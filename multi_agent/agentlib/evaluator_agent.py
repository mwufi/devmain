from .base_agent import BaseAgent
from typing import Dict, List
from agents import Runner

class EvaluatorAgent(BaseAgent):
    def __init__(self):
        instructions = """
        You are an Evaluator agent. Your role is to:
        1. Evaluate the quality and completeness of results
        2. Assess relevance to the original task
        3. Provide constructive feedback and suggestions
        4. Calculate overall scores based on multiple metrics
        """
        super().__init__("Evaluator", "Results Evaluator", instructions)
        
    async def evaluate(self, results: Dict) -> Dict:
        """Evaluate results from a helper agent"""
        await self.log_event("evaluate_results", {"results": results})
        
        # Get evaluation from the agent
        result = await Runner.run(self, input=f"Evaluate these results: {results}")
        
        # Basic evaluation metrics
        evaluation = {
            "completeness": await self._evaluate_completeness(results),
            "quality": await self._evaluate_quality(results),
            "relevance": await self._evaluate_relevance(results),
            "suggestions": await self._generate_suggestions(results),
            "agent_evaluation": result.final_output
        }
        
        return {
            "evaluation": evaluation,
            "overall_score": self._calculate_overall_score(evaluation)
        }
        
    async def _evaluate_completeness(self, results: Dict) -> float:
        """Evaluate how complete the results are"""
        result = await Runner.run(self, input=f"Evaluate completeness of: {results}")
        response = result.final_output.lower()
        
        score = 0.5  # Base score
        if "complete" in response:
            score += 0.3
        if "missing" not in response:
            score += 0.2
            
        return min(1.0, score)
        
    async def _evaluate_quality(self, results: Dict) -> float:
        """Evaluate the quality of the results"""
        result = await Runner.run(self, input=f"Evaluate quality of: {results}")
        response = result.final_output.lower()
        
        score = 0.5  # Base score
        if "high quality" in response or "excellent" in response:
            score += 0.3
        if "detailed" in response:
            score += 0.2
            
        return min(1.0, score)
        
    async def _evaluate_relevance(self, results: Dict) -> float:
        """Evaluate how relevant the results are to the task"""
        result = await Runner.run(self, input=f"Evaluate relevance of: {results}")
        response = result.final_output.lower()
        
        score = 0.5  # Base score
        if "relevant" in response:
            score += 0.3
        if "on topic" in response:
            score += 0.2
            
        return min(1.0, score)
        
    async def _generate_suggestions(self, results: Dict) -> List[str]:
        """Generate suggestions for improvement"""
        result = await Runner.run(self, input=f"Provide suggestions for improving: {results}")
        response = result.final_output
        
        # Split response into suggestions
        suggestions = [s.strip() for s in response.split('\n') if s.strip()]
        return suggestions
        
    def _calculate_overall_score(self, evaluation: Dict) -> float:
        """Calculate an overall score from the evaluation"""
        weights = {
            "completeness": 0.3,
            "quality": 0.4,
            "relevance": 0.3
        }
        
        return sum(
            evaluation[metric] * weight
            for metric, weight in weights.items()
        ) 