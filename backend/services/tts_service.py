"""TTS 语音合成服务（Edge-TTS 免费方案）"""
import io
import asyncio
import edge_tts
from config import settings

# 适合儿童的英语女声
VOICE = "en-US-JennyNeural"

# 回退语音列表
FALLBACK_VOICES = [
    "en-US-AriaNeural",
    "en-GB-SoniaNeural",
    "en-US-AnaNeural",
]


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """
    将文字转为语音，返回 MP3 字节流
    使用 Microsoft Edge TTS（免费，无需 API Key）
    """
    selected_voice = voice or VOICE

    try:
        communicate = edge_tts.Communicate(text, selected_voice)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        return b"".join(audio_chunks)
    except Exception as e:
        # 尝试回退语音
        for fallback in FALLBACK_VOICES:
            try:
                if fallback == selected_voice:
                    continue
                communicate = edge_tts.Communicate(text, fallback)
                audio_chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                return b"".join(audio_chunks)
            except Exception:
                continue
        raise RuntimeError(f"TTS failed: {e}")
