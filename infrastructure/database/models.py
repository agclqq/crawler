"""SQLAlchemy 数据库模型"""

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class CrawlerTaskModel(Base):
    """爬虫任务数据库模型"""
    __tablename__ = "crawler_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String(2048), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    content = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    task_metadata = Column("metadata", JSON, nullable=True, default=dict)  # 使用 task_metadata 作为属性名，但数据库列名仍为 metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

