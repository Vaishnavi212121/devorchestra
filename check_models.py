"""
Base Agent Class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import os
import logging
import google.generativeai as genai
from core.redis_manager import get_redis_bus
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.redis_bus = get_redis_bus()
        self.logger = logging.getLogger(agent_id)
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # 👇 FIXED: Using a model that actually exists in your list!
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                self.logger.error(f"Failed to configure AI model: {e}")
                self.model = None
        else:
            self.model = None

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return await self.execute_task(task)

    async def generate_response(self, prompt: str) -> str:
        if not self.model:
            raise Exception("AI Model is not initialized. Check GOOGLE_API_KEY.")
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"AI Generation failed: {e}")
            raise

    async def _publish_status(self, task_id: str, agent_id: str, status: str, data: Dict = None):
        if not data: data = {}
        await self.redis_bus.publish_task_status(task_id, agent_id, status, data)
        message = {
            "task_id": task_id, "agent_id": agent_id, "status": status,
            "data": data, "timestamp": datetime.now().isoformat()
        }
        await self.redis_bus.store_task_history(task_id, message)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "id": self.agent_id,
            "status": "active",
            "last_active": datetime.now().isoformat(),
            "model": "gemini-pro" if self.model else "none"
        }