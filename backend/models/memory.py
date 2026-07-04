"""记忆模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, Enum, DateTime
from db.connection import Base


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1)
    memory_type = Column(
        Enum(
            "vocab_mastered",
            "vocab_weak",
            "grammar_weak",
            "pronunciation_issue",
            "learning_preference",
            "interest_topic",
        ),
        nullable=False,
        comment="记忆类型",
    )
    memory_key = Column(String(200), name="`key`", nullable=False, comment="记忆关键词")
    memory_value = Column(Text, name="`value`", comment="记忆内容")
    confidence = Column(Float, default=0.5, comment="置信度")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
