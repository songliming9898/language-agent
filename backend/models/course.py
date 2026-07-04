"""课程相关数据模型"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Enum, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship
from db.connection import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grade = Column(String(20), nullable=False, comment="年级")
    semester = Column(String(20), nullable=False, comment="学期")
    version = Column(String(50), default="2024", comment="教材版本")
    created_at = Column(DateTime, default=datetime.utcnow)

    units = relationship("CourseUnit", back_populates="course", lazy="selectin")


class CourseUnit(Base):
    __tablename__ = "course_units"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    unit_name = Column(String(100), nullable=False, comment="单元名称")
    unit_order = Column(Integer, nullable=False, comment="单元序号")
    description = Column(Text, comment="单元描述")
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="units")
    sentences = relationship("Sentence", back_populates="unit", lazy="selectin")


class Sentence(Base):
    __tablename__ = "sentences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_id = Column(Integer, ForeignKey("course_units.id", ondelete="CASCADE"), nullable=False)
    sentence_text = Column(Text, nullable=False, comment="英文句子")
    sentence_order = Column(Integer, nullable=False, comment="排序")
    audio_url = Column(String(500), comment="标准发音音频URL")
    translation = Column(String(500), comment="中文翻译")
    difficulty = Column(Enum("easy", "medium", "hard"), default="easy")
    created_at = Column(DateTime, default=datetime.utcnow)

    unit = relationship("CourseUnit", back_populates="sentences")
