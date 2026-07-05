"""TTS 语音合成服务（Microsoft Edge TTS）"""
import asyncio
import edge_tts
from config import settings

# 中英文音色映射
VOICE_MAP = {
    "en": "en-US-JennyNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "default": "en-US-JennyNeural",
}


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """
    将文字转为语音，返回 MP3 字节流
    使用 Microsoft Edge TTS（免费，无需 API Key）
    """
    tts_voice = voice or VOICE_MAP["default"]

    print(f"[TTS] Edge TTS synthesizing: {text[:60]}... (voice={tts_voice})")

    try:
        communicate = edge_tts.Communicate(text, tts_voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if audio_data:
            print(f"[TTS] Success: {len(audio_data)} bytes")
            return audio_data
        else:
            print("[TTS] No audio data received")
            return b""

    except Exception as e:
        print(f"[TTS] Error: {type(e).__name__}: {e}")
        return b""
