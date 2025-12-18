"""
ADO PARSER - DYNAMIC AI-POWERED VERSION
Uses Gemini AI to intelligently parse user stories into requirements.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any
import json
import asyncio

class ADOParserAgent(BaseAgent):
    def __init__(self):
        super().__init__("ado_parser")
        self.ado_enabled = True 

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id", "unknown")
        user_story = task.get("user_story", "") or ""
        
        await self._publish_status(task_id, self.agent_id, "parsing", {"story_length": len(user_story)})
        
        # ✅ USE AI TO INTELLIGENTLY PARSE REQUIREMENTS
        prompt = f"""Analyze this user story and break it into technical requirements:

USER STORY: {user_story}

Extract and return ONLY a valid JSON object with these exact keys:
{{
    "frontend_requirements": "Detailed React/UI requirements with specific components needed",
    "backend_requirements": "Detailed API/Backend requirements with specific endpoints",
    "database_requirements": "Detailed Database schema requirements with specific tables and fields"
}}

Be specific about:
- Frontend: What UI components, forms, tables, buttons, layouts are needed
- Backend: What API endpoints (GET/POST/PUT/DELETE), business logic, validations
- Database: What tables, columns, relationships, constraints

Return ONLY the JSON object, no markdown, no explanation."""

        try:
            # Use the real AI to parse requirements
            response = await self.generate_response(prompt)
            
            # Clean the response
            cleaned = response.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            result_json = json.loads(cleaned)
            
            # Validate required keys exist
            required_keys = ["frontend_requirements", "backend_requirements", "database_requirements"]
            for key in required_keys:
                if key not in result_json:
                    result_json[key] = f"Create implementation for: {user_story}"
            
            await self._publish_status(task_id, self.agent_id, "completed", {})
            return {"status": "success", "result": result_json}
            
        except json.JSONDecodeError as e:
            # Fallback if AI returns invalid JSON
            print(f"⚠️ JSON parse error: {e}")
            result_json = {
                "frontend_requirements": f"Create a React application for: {user_story}",
                "backend_requirements": f"Create a REST API backend for: {user_story}",
                "database_requirements": f"Create a database schema for: {user_story}"
            }
            await self._publish_status(task_id, self.agent_id, "completed", {})
            return {"status": "success", "result": result_json}
            
        except Exception as e:
            print(f"❌ Parser error: {e}")
            await self._publish_status(task_id, self.agent_id, "failed", {"error": str(e)})
            return {"status": "failed", "error": str(e)}

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return await self.execute_task(task)