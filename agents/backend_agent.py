from agents.base_agent import BaseAgent
from typing import Dict, Any
import json

class BackendAgent(BaseAgent):
    def __init__(self):
        super().__init__("backend_agent")

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id", "unknown")
        requirements = task.get("requirements", "")
        await self._publish_status(task_id, self.agent_id, "starting", {})

        prompt = f'''
        You are an expert FastAPI developer.
        Generate a Python API for: {requirements}
        Return ONLY valid JSON: {{ "api_code": "code...", "endpoints": [] }}
        '''

        try:
            response = await self.generate_response(prompt)
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return {"status": "success", "result": json.loads(cleaned)}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
