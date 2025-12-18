"""
Fixed database.py - Simple SQLite database manager
"""
import sqlite3
import os
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class DatabaseManager:
    def __init__(self, db_path="devorchestra.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
        logger.info(f"✅ Database connected: {db_path}")
    
    def _create_tables(self):
        """Create necessary tables"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_story TEXT,
                status TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_tasks_timestamp ON tasks(timestamp);
        """)
        self.conn.commit()
    
    def add_task(self, task_id: str, user_story: str, status: TaskStatus):
        """Add a new task"""
        try:
            self.conn.execute(
                "INSERT INTO tasks (id, user_story, status) VALUES (?, ?, ?)",
                (task_id, user_story, status.value)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error adding task: {e}")
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: str = None):
        """Update task status and result"""
        try:
            if result:
                self.conn.execute(
                    "UPDATE tasks SET status = ?, result = ? WHERE id = ?",
                    (status.value, result, task_id)
                )
            else:
                self.conn.execute(
                    "UPDATE tasks SET status = ? WHERE id = ?",
                    (status.value, task_id)
                )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error updating task: {e}")
    
    def get_task(self, task_id: str):
        """Get task by ID"""
        cursor = self.conn.execute(
            "SELECT id, user_story, status, result, timestamp FROM tasks WHERE id = ?",
            (task_id,)
        )
        return cursor.fetchone()
    
    def get_latest_task(self):
        """Get the most recent task"""
        cursor = self.conn.execute(
            "SELECT id, user_story, status, result, timestamp FROM tasks ORDER BY timestamp DESC LIMIT 1"
        )
        return cursor.fetchone()

# Global instance
_db_manager = None

def get_db_manager():
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager