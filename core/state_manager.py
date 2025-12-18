"""PostgreSQL Database Manager for State Storage."""
import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
import enum

Base = declarative_base()

class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(String(50), primary_key=True)
    user_story = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self):
        self.logger = logging.getLogger("database")
        database_url = os.getenv("DATABASE_URL", "sqlite:///devorchestra.db")
        
        try:
            self.engine = create_engine(database_url, echo=False)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            self.logger.info(f"Database connected: {database_url}")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise

_db_manager = None

def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
