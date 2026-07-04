"""学习进度 & 记忆 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.connection import get_db
from models.progress import UserProgress
from models.memory import MemoryRecord
from services.memory_service import get_memory_context
from config import settings

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress")
def get_overall_progress(db: Session = Depends(get_db)):
    """获取学习进度总览"""
    uid = settings.DEMO_USER_ID

    total = db.query(func.count(UserProgress.id)).filter(UserProgress.user_id == uid).scalar() or 0
    mastered = (
        db.query(func.count(UserProgress.id))
        .filter(UserProgress.user_id == uid, UserProgress.mastered == True)
        .scalar()
        or 0
    )
    total_practices = (
        db.query(func.sum(UserProgress.practice_count))
        .filter(UserProgress.user_id == uid)
        .scalar()
        or 0
    )

    return {
        "code": 0,
        "data": {
            "total_sentences": total,
            "mastered_count": mastered,
            "total_practices": total_practices,
            "mastery_rate": round(mastered / total * 100, 1) if total > 0 else 0,
        },
    }


@router.get("/progress/unit/{unit_id}")
def get_unit_progress(unit_id: int, db: Session = Depends(get_db)):
    """获取某单元的学习进度"""
    uid = settings.DEMO_USER_ID

    # 获取单元所有句子的进度
    from models.course import Sentence
    sentences = (
        db.query(Sentence)
        .filter(Sentence.unit_id == unit_id)
        .order_by(Sentence.sentence_order)
        .all()
    )

    result = []
    for s in sentences:
        progress = (
            db.query(UserProgress)
            .filter(UserProgress.user_id == uid, UserProgress.sentence_id == s.id)
            .first()
        )
        result.append({
            "sentence_id": s.id,
            "sentence_text": s.sentence_text,
            "practice_count": progress.practice_count if progress else 0,
            "score_avg": (
                round(
                    (progress.score_accuracy + progress.score_fluency + progress.score_completeness) / 3,
                    1,
                )
                if progress
                else 0
            ),
            "mastered": progress.mastered if progress else False,
        })

    return {"code": 0, "data": result}


@router.get("/memory/summary")
def get_memory_summary(db: Session = Depends(get_db)):
    """获取用户记忆摘要"""
    uid = settings.DEMO_USER_ID

    records = db.query(MemoryRecord).filter(MemoryRecord.user_id == uid).all()

    summary = {}
    for r in records:
        t = r.memory_type
        if t not in summary:
            summary[t] = []
        summary[t].append({"key": r.memory_key, "value": r.memory_value, "confidence": r.confidence})

    context = get_memory_context(db, uid)

    return {
        "code": 0,
        "data": {
            "records": summary,
            "context_text": context,
        },
    }
