from agents.base_agent import BaseAgent
from typing import Dict, Any
import json

class DatabaseAgent(BaseAgent):
    def __init__(self):
        super().__init__("database_agent")

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id", "unknown")
        requirements = task.get("requirements", "")
        await self._publish_status(task_id, self.agent_id, "starting", {})

        prompt = f'''
        You are a Database Architect.
        Generate PostgreSQL schema for: {requirements}
        Return ONLY valid JSON: {{ "schema_sql": "CREATE TABLE...", "tables": [] }}
        '''

        try:
            response = await self.generate_response(prompt)
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return {"status": "success", "result": json.loads(cleaned)}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
