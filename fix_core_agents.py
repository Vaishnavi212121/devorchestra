import os

# 1. FRONTEND AGENT
frontend_code = """from agents.base_agent import BaseAgent
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
"""

# 2. BACKEND AGENT (The one crashing)
backend_code = """from agents.base_agent import BaseAgent
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
"""

# 3. DATABASE AGENT
database_code = """from agents.base_agent import BaseAgent
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
"""

# Write files
files = {
    "agents/frontend_agent.py": frontend_code,
    "agents/backend_agent.py": backend_code,
    "agents/database_agent.py": database_code
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Repaired {path}")