"""TTS 语音合成服务（火山引擎豆包 TTS）"""
import json
import uuid
import asyncio
import aiohttp
from config import settings


DOUBAO_API_URL = "https://openspeech.bytedance.com/api/v1/tts"


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """
    将文字转为语音，返回 MP3 字节流
    使用火山引擎豆包 TTS
    """
    api_key = settings.DOUBAO_API_KEY
    tts_voice = voice or settings.DOUBAO_VOICE

    if not api_key:
        print("[TTS] Doubao API Key not configured")
        return b""

    print(f"[TTS] Doubao synthesizing: {text[:60]}...")

    headers = {
        "Authorization": f"Bearer;{api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "app": {
            "appid": "kids_english",
            "token": api_key,
            "cluster": "volcano_tts",
        },
        "user": {
            "uid": "kids_english_user",
        },
        "audio": {
            "voice_type": tts_voice,
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                DOUBAO_API_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    print(f"[TTS] Doubao returned {resp.status}: {body[:200]}")
                    return b""

                result = await resp.json()
                code = result.get("code", -1)
                if code != 3000:
                    print(f"[TTS] Doubao error code={code}, msg={result.get('message', '')}")
                    return b""

                audio_b64 = result.get("data", "")
                if not audio_b64:
                    print("[TTS] Doubao returned empty audio data")
                    return b""

                import base64
                audio_data = base64.b64decode(audio_b64)
                print(f"[TTS] Success: {len(audio_data)} bytes")
                return audio_data

    except Exception as e:
        print(f"[TTS] Error: {type(e).__name__}: {e}")
        return b""
