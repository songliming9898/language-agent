"""学习进度模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from db.connection import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1)
    sentence_id = Column(Integer, ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False)
    practice_count = Column(Integer, default=0, comment="练习次数")
    score_accuracy = Column(Float, default=0, comment="音准分")
    score_fluency = Column(Float, default=0, comment="流利度分")
    score_completeness = Column(Float, default=0, comment="完整度分")
    last_practice_at = Column(DateTime, nullable=True)
    mastered = Column(Boolean, default=False, comment="是否掌握")
    created_at = Column(DateTime, default=datetime.utcnow)
