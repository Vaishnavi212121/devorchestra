"""
core/redis_manager.py
Redis Communication Bus for Agent Pub/Sub.
"""
import redis.asyncio as redis
import json
import os
import logging
from typing import Callable, Any
from datetime import datetime

class RedisMessageBus:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.logger = logging.getLogger("redis_bus")
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self.logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            self.logger.error(f"Redis connection failed: {e}")
            self.redis = None

    async def publish(self, channel: str, message: dict):
        if self.redis:
            try:
                await self.redis.publish(channel, json.dumps(message))
            except Exception as e:
                self.logger.error(f"Failed to publish to {channel}: {e}")

    async def subscribe(self, channel: str, callback: Callable):
        if self.redis:
            try:
                pubsub = self.redis.pubsub()
                await pubsub.subscribe(channel)
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        data = json.loads(message["data"])
                        await callback(data)
            except Exception as e:
                self.logger.error(f"Subscription failed: {e}")

    async def publish_task_status(self, task_id: str, agent_id: str, status: str, details: dict = None):
        message = {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        await self.publish(f"task:{task_id}", message)
        await self.publish("global:tasks", message)

    async def store_task_history(self, task_id: str, message: dict):
        if self.redis:
            try:
                key = f"history:{task_id}"
                await self.redis.lpush(key, json.dumps(message))
                await self.redis.expire(key, 86400)
            except Exception as e:
                self.logger.error(f"Failed to store history: {e}")

    async def get_task_history(self, task_id: str) -> list:
        if self.redis:
            try:
                key = f"history:{task_id}"
                history = await self.redis.lrange(key, 0, -1)
                return [json.loads(h) for h in history]
            except Exception as e:
                self.logger.error(f"Failed to get history: {e}")
        return []

    # 👇 THIS IS THE MISSING FUNCTION 👇
    def health_check(self) -> bool:
        """Check if Redis connection is active."""
        if not self.redis:
            return False
        return True

# Global instance
_redis_bus = RedisMessageBus()

def get_redis_bus():
    return _redis_bus