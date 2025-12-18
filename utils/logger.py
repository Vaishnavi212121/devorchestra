import asyncio
from datetime import datetime, timedelta

class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logging.getLogger(agent_id)
        self.status = "idle"
        self.metrics = {
            "tasks_completed": 0, 
            "tasks_failed": 0, 
            "total_execution_time": 0.0
        }
        
        # Rate limiting
        self.rate_limit = 10  # Max 10 requests per minute
        self.rate_window = 60  # seconds
        self.request_times = []
    
    async def _check_rate_limit(self):
        """Enforce rate limiting"""
        now = datetime.now()
        
        # Remove old requests outside window
        self.request_times = [
            t for t in self.request_times 
            if now - t < timedelta(seconds=self.rate_window)
        ]
        
        # Check if limit exceeded
        if len(self.request_times) >= self.rate_limit:
            wait_time = (self.request_times[0] + 
                        timedelta(seconds=self.rate_window) - now).total_seconds()
            self.logger.warning(f"Rate limit reached. Waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        # Record this request
        self.request_times.append(now)