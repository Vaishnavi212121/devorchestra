from agents.base_agent import BaseAgent
from typing import Dict, Any
import json

class FrontendAgent(BaseAgent):
    def __init__(self):
        super().__init__("frontend_agent")

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id", "unknown")
        requirements = task.get("requirements", "")
        
        await self._publish_status(task_id, self.agent_id, "starting", {})

        prompt = f'''
        You are an expert React developer.
        Generate a React component for: {requirements}
        Return ONLY valid JSON: {{ "component_code": "code...", "dependencies": [] }}
        '''

        try:
            response = await self.generate_response(prompt)
            # Cleanup markdown formatting
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return {"status": "success", "result": json.loads(cleaned)}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
