"""对练相关 API — 课程对练 & 自由对话"""
import uuid
import json
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from db.connection import get_db
from models.conversation import Conversation
from models.progress import UserProgress
from services.llm_service import chat, evaluate_pronunciation, chat_stream
from services.memory_service import get_memory_context, analyze_and_remember
from services.tts_service import text_to_speech
from services.asr_service import speech_to_text
from config import settings

router = APIRouter(prefix="/api/practice", tags=["practice"])


# ============ 课程对练 ============

@router.post("/evaluate")
async def evaluate_sentence(
    audio: UploadFile = File(...),
    sentence_id: int = Form(...),
    sentence_text: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    课程跟读评分：
    1. 接收用户录音
    2. ASR 转文字
    3. 对比标准句子评分
    4. 记录进度
    """
    audio_bytes = await audio.read()

    # ASR 识别
    transcript = await speech_to_text(audio_bytes, audio.filename or "audio.webm")

    # LLM 评分
    if transcript:
        result = await evaluate_pronunciation(sentence_text, transcript)
    else:
        result = {
            "accuracy": 0,
            "fluency": 0,
            "completeness": 0,
            "feedback": "Sorry, I couldn't hear you clearly. Please try again! 🎤",
        }

    # 更新进度
    uid = settings.DEMO_USER_ID
    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == uid, UserProgress.sentence_id == sentence_id)
        .first()
    )

    if progress:
        progress.practice_count += 1
        # 加权平均
        n = progress.practice_count
        progress.score_accuracy = (progress.score_accuracy * (n - 1) + result.get("accuracy", 0)) / n
        progress.score_fluency = (progress.score_fluency * (n - 1) + result.get("fluency", 0)) / n
        progress.score_completeness = (progress.score_completeness * (n - 1) + result.get("completeness", 0)) / n
        avg = (progress.score_accuracy + progress.score_fluency + progress.score_completeness) / 3
        progress.mastered = avg >= 80
    else:
        progress = UserProgress(
            user_id=uid,
            sentence_id=sentence_id,
            practice_count=1,
            score_accuracy=result.get("accuracy", 0),
            score_fluency=result.get("fluency", 0),
            score_completeness=result.get("completeness", 0),
        )
        db.add(progress)

    db.commit()

    return {
        "code": 0,
        "data": {
            "transcript": transcript,
            "scores": {
                "accuracy": result.get("accuracy", 0),
                "fluency": result.get("fluency", 0),
                "completeness": result.get("completeness", 0),
            },
            "feedback": result.get("feedback", "Good try! 👍"),
        },
    }


# ============ 自由对话 ============

@router.post("/chat")
async def free_chat(
    text: str = Form(""),
    audio: UploadFile = File(None),
    session_id: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    自由对话：
    1. 接收文字或语音
    2. 获取用户记忆上下文
    3. LLM 生成回复
    4. TTS 合成语音
    5. 存储对话 + 更新记忆
    """
    uid = settings.DEMO_USER_ID

    # 处理输入
    user_text = text
    print(f"[DEBUG /chat] text={text!r}, audio={audio}, audio.filename={audio.filename if audio else None}, audio.size={audio.size if audio else None}")
    if audio and audio.filename and audio.size and audio.size > 0:
        audio_bytes = await audio.read()
        print(f"[DEBUG /chat] read {len(audio_bytes)} bytes from audio")
        if audio_bytes:
            user_text = await speech_to_text(audio_bytes, audio.filename or "audio.webm")
            print(f"[DEBUG /chat] ASR result: {user_text!r}")

    if not user_text:
        print("[DEBUG /chat] No text or audio, returning error")
        return {"code": 1, "message": "No text or audio provided"}

    # 创建或使用已有 session
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    # 保存用户消息
    user_msg = Conversation(
        user_id=uid,
        session_id=session_id,
        mode="free_talk",
        role="user",
        message_text=user_text,
    )
    db.add(user_msg)
    db.commit()

    # 获取记忆上下文
    memory_ctx = get_memory_context(db, uid)

    # 获取最近对话历史（作为 LLM 上下文）
    recent = (
        db.query(Conversation)
        .filter(Conversation.user_id == uid, Conversation.session_id == session_id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
        .all()
    )
    messages = []
    for msg in reversed(recent):
        messages.append({"role": msg.role, "content": msg.message_text})

    # LLM 回复
    reply = await chat(messages, memory_ctx)

    # 保存助手消息
    assistant_msg = Conversation(
        user_id=uid,
        session_id=session_id,
        mode="free_talk",
        role="assistant",
        message_text=reply,
    )
    db.add(assistant_msg)
    db.commit()

    # 分析对话，更新记忆
    analyze_and_remember(db, user_text, reply, uid)

    # TTS 合成语音
    try:
        audio_data = await text_to_speech(reply)
        audio_base64 = None
        if audio_data:
            import base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
    except Exception:
        audio_base64 = None

    return {
        "code": 0,
        "data": {
            "session_id": session_id,
            "user_text": user_text,
            "reply": reply,
            "audio_base64": audio_base64,
        },
    }


@router.post("/chat/stream")
async def free_chat_stream(
    text: str = Form(""),
    session_id: str = Form(""),
    db: Session = Depends(get_db),
):
    """流式自由对话（SSE）"""
    uid = settings.DEMO_USER_ID

    if not text or not session_id:
        return {"code": 1, "message": "Missing text or session_id"}

    # 保存用户消息
    user_msg = Conversation(
        user_id=uid,
        session_id=session_id,
        mode="free_talk",
        role="user",
        message_text=text,
    )
    db.add(user_msg)
    db.commit()

    memory_ctx = get_memory_context(db, uid)
    recent = (
        db.query(Conversation)
        .filter(Conversation.user_id == uid, Conversation.session_id == session_id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
        .all()
    )
    messages = [{"role": msg.role, "content": msg.message_text} for msg in reversed(recent)]

    async def event_generator():
        full_reply = ""
        async for token in chat_stream(messages, memory_ctx):
            full_reply += token
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

        # 后台保存
        assistant_msg = Conversation(
            user_id=uid,
            session_id=session_id,
            mode="free_talk",
            role="assistant",
            message_text=full_reply,
        )
        db.add(assistant_msg)
        db.commit()
        analyze_and_remember(db, text, full_reply, uid)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============ 会话管理 ============

@router.post("/session/start")
def start_session(mode: str = Form("free_talk"), db: Session = Depends(get_db)):
    """开始新会话"""
    session_id = str(uuid.uuid4())[:8]

    # 保存系统消息
    sys_msg = Conversation(
        user_id=settings.DEMO_USER_ID,
        session_id=session_id,
        mode=mode,
        role="system",
        message_text=f"Session started: {mode}",
    )
    db.add(sys_msg)
    db.commit()

    return {"code": 0, "data": {"session_id": session_id}}


@router.get("/session/{session_id}/history")
def get_history(session_id: str, db: Session = Depends(get_db)):
    """获取对话历史"""
    messages = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == settings.DEMO_USER_ID,
            Conversation.session_id == session_id,
            Conversation.role.in_(["user", "assistant"]),
        )
        .order_by(Conversation.created_at.asc())
        .all()
    )

    return {
        "code": 0,
        "data": [
            {
                "id": m.id,
                "role": m.role,
                "text": m.message_text,
                "time": m.created_at.isoformat() if m.created_at else "",
            }
            for m in messages
        ],
    }


# ============ TTS 单独接口 ============

@router.post("/tts")
async def synthesize_speech(text: str = Form(...)):
    """文字转语音"""
    try:
        audio_data = await text_to_speech(text)
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline"},
        )
    except Exception as e:
        return {"code": 1, "message": str(e)}
