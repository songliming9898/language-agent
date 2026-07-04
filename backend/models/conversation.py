"""对话历史模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, Enum, DateTime, ForeignKey
from db.connection import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, comment="用户ID")
    session_id = Column(String(64), nullable=False, comment="会话ID")
    mode = Column(Enum("course", "free_talk"), nullable=False, comment="对练模式")
    course_unit_id = Column(Integer, ForeignKey("course_units.id"), nullable=True)
    role = Column(Enum("user", "assistant", "system"), nullable=False)
    message_text = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
