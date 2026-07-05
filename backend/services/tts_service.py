"""TTS 语音合成服务（pyttsx3 离线方案）"""
import io
import os
import tempfile
import asyncio
import concurrent.futures
from config import settings


def _synthesize_sync(text: str) -> bytes:
    """同步合成语音（在 executor 中运行）"""
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)    # 语速
    engine.setProperty("volume", 0.9)  # 音量

    # 尝试设置英语女声
    voices = engine.getProperty("voices")
    for v in voices:
        if "english" in v.name.lower() or "zira" in v.name.lower() or "en" in v.id.lower():
            engine.setProperty("voice", v.id)
            break

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    engine.save_to_file(text, tmp_path)
    engine.runAndWait()

    with open(tmp_path, "rb") as f:
        data = f.read()

    os.unlink(tmp_path)
    return data


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """
    将文字转为语音，返回 MP3 字节流
    使用 pyttsx3 离线引擎（免费，无需网络，无需 API Key）
    """
    print(f"[TTS] pyttsx3 synthesizing: {text[:50]}...")
    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            data = await loop.run_in_executor(pool, _synthesize_sync, text)
        print(f"[TTS] Success: {len(data)} bytes")
        return data
    except Exception as e:
        print(f"[TTS] Error: {type(e).__name__}: {e}")
        return b""
