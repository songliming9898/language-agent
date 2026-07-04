"""记忆管理服务"""
from sqlalchemy.orm import Session
from models.memory import MemoryRecord
from config import settings


def get_user_memories(db: Session, user_id: int = None) -> list[MemoryRecord]:
    """获取用户所有记忆"""
    uid = user_id or settings.DEMO_USER_ID
    return db.query(MemoryRecord).filter(MemoryRecord.user_id == uid).all()


def get_memory_context(db: Session, user_id: int = None) -> str:
    """获取格式化的记忆上下文，用于注入 System Prompt"""
    from services.llm_service import build_memory_context
    records = get_user_memories(db, user_id)
    return build_memory_context(records)


def upsert_memory(
    db: Session,
    memory_type: str,
    key: str,
    value: str = "",
    confidence: float = 0.5,
    user_id: int = None,
) -> MemoryRecord:
    """插入或更新记忆记录"""
    uid = user_id or settings.DEMO_USER_ID

    record = (
        db.query(MemoryRecord)
        .filter(
            MemoryRecord.user_id == uid,
            MemoryRecord.memory_type == memory_type,
            MemoryRecord.memory_key == key,
        )
        .first()
    )

    if record:
        record.memory_value = value or record.memory_value
        record.confidence = max(record.confidence, confidence)
    else:
        record = MemoryRecord(
            user_id=uid,
            memory_type=memory_type,
            memory_key=key,
            memory_value=value,
            confidence=confidence,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


def analyze_and_remember(
    db: Session,
    user_text: str,
    assistant_text: str,
    user_id: int = None,
):
    """从对话中分析并提取记忆点（简化版：基于关键词匹配）"""
    uid = user_id or settings.DEMO_USER_ID

    # 简单规则：检测用户文本中的常见三年级词汇
    common_words = {
        "hello", "hi", "goodbye", "bye", "thank", "please", "sorry",
        "apple", "banana", "cat", "dog", "bird", "fish", "pig", "duck",
        "red", "blue", "green", "yellow", "white", "black",
        "one", "two", "three", "four", "five",
        "mother", "father", "sister", "brother", "family",
        "head", "eye", "ear", "nose", "mouth", "hand",
        "milk", "bread", "egg", "rice", "cake", "water",
        "big", "small", "long", "short", "happy", "sad",
        "like", "love", "eat", "drink", "run", "jump",
    }

    words = set(user_text.lower().split())
    for word in words:
        clean_word = word.strip(",.!?;:'\"")
        if clean_word in common_words:
            upsert_memory(
                db,
                memory_type="vocab_mastered",
                key=clean_word,
                value=f"Student used '{clean_word}' in conversation",
                confidence=0.6,
                user_id=uid,
            )
