"""Integration Validator Agent."""
from agents.base_agent import BaseAgent
from typing import Dict, Any
import json

class IntegrationAgent(BaseAgent):
    def __init__(self):
        super().__init__("integration")
        # ✅ FIX: Do NOT manually set self.model here. 
        # BaseAgent handles it automatically with the correct model.

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Verify frontend-backend compatibility."""
        frontend_code = task.get("frontend_code", "")
        backend_code = task.get("backend_code", "")

        prompt = f"""Analyze the integration between this Frontend and Backend.

FRONTEND CODE:
{frontend_code[:2000]}... (truncated)

BACKEND CODE:
{backend_code[:2000]}... (truncated)

VERIFY:
1. Do API endpoints match? (e.g., fetch('/api/login') vs @app.post('/api/login'))
2. Do HTTP methods match? (GET vs POST)
3. Do request bodies match expected schemas?
4. Are response formats handled correctly?

OUTPUT JSON:
{{
    "compatible": <boolean>,
    "compatibility_score": <0-100>,
    "mismatches": ["list", "of", "route/data", "mismatches"],
    "integration_plan": "Short summary of how they connect"
}}
"""

        try:
            # Use the BaseAgent's robust generate method
            response = await self.generate_response(prompt)
            # Clean up potential markdown formatting
            text = response.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            return {
                "compatible": False,
                "compatibility_score": 0,
                "mismatches": [f"Analysis failed: {str(e)}"]
            }