"""课程相关 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.connection import get_db
from models.course import Course, CourseUnit, Sentence

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("")
def list_courses(db: Session = Depends(get_db)):
    """获取所有课程"""
    courses = db.query(Course).order_by(Course.id).all()
    return {
        "code": 0,
        "data": [
            {
                "id": c.id,
                "grade": c.grade,
                "semester": c.semester,
                "version": c.version,
            }
            for c in courses
        ],
    }


@router.get("/{course_id}/units")
def list_units(course_id: int, db: Session = Depends(get_db)):
    """获取课程下的所有单元"""
    units = (
        db.query(CourseUnit)
        .filter(CourseUnit.course_id == course_id)
        .order_by(CourseUnit.unit_order)
        .all()
    )
    return {
        "code": 0,
        "data": [
            {
                "id": u.id,
                "unit_name": u.unit_name,
                "unit_order": u.unit_order,
                "description": u.description,
            }
            for u in units
        ],
    }


@router.get("/units/{unit_id}/sentences")
def list_sentences(unit_id: int, db: Session = Depends(get_db)):
    """获取单元下的所有句子"""
    sentences = (
        db.query(Sentence)
        .filter(Sentence.unit_id == unit_id)
        .order_by(Sentence.sentence_order)
        .all()
    )
    return {
        "code": 0,
        "data": [
            {
                "id": s.id,
                "sentence_text": s.sentence_text,
                "sentence_order": s.sentence_order,
                "translation": s.translation,
                "difficulty": s.difficulty,
            }
            for s in sentences
        ],
    }
