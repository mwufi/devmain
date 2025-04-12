from typing import Dict, List, Optional
import json
from datetime import datetime
import os
from agents import Agent

class BaseAgent(Agent):
    def __init__(self, name: str, role: str, instructions: str = ""):
        super().__init__(
            name=name,
            instructions=instructions
        )
        self.role = role
        self.event_log: List[Dict] = []
        self.context: Dict = {}
        
    async def log_event(self, event_type: str, details: Dict):
        """Log an event to the event log"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details
        }
        self.event_log.append(event)
        await self._save_event_log()
        
    async def _save_event_log(self):
        """Save the event log to a file"""
        os.makedirs("data", exist_ok=True)
        with open(f"data/{self.name}_eventlog.json", "w") as f:
            json.dump(self.event_log, f, indent=2)
            
    async def load_event_log(self):
        """Load the event log from a file"""
        try:
            with open(f"data/{self.name}_eventlog.json", "r") as f:
                self.event_log = json.load(f)
        except FileNotFoundError:
            self.event_log = []
            
    def get_context(self) -> Dict:
        """Get the current context of the agent"""
        return self.context
    
    def update_context(self, new_context: Dict):
        """Update the agent's context"""
        self.context.update(new_context)
        
    def clear_context(self):
        """Clear the agent's context"""
        self.context = {} 