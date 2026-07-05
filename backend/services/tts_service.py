"""TTS 语音合成服务（阿里云语音合成）"""
import json
import time
import traceback
import aiohttp
from config import settings

# 阿里云 Token 换取地址
TOKEN_URL = "https://nls-meta.cn-shanghai.aliyuncs.com/pop/2018-05-18/tokens"
# 语音合成地址
TTS_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts"

VOICE = "zhiyao"        # 儿童英语女声
FORMAT = "mp3"
SAMPLE_RATE = 16000

# Token 缓存（避免每次请求都换）
_token_cache = {"token": "", "expire_time": 0}


async def _get_token() -> str:
    """获取阿里云语音合成 Token（带缓存）"""
    global _token_cache

    # 如果 token 还有效（提前 60 秒刷新）
    if _token_cache["token"] and time.time() < _token_cache["expire_time"] - 60:
        return _token_cache["token"]

    access_key_id = settings.ALIYUN_AK_ID
    access_key_secret = settings.ALIYUN_AK_SECRET

    print(f"[TTS Token] Requesting new token...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TOKEN_URL,
                json={},
                headers={
                    "Content-Type": "application/json",
                    "AccessKeyId": access_key_id,
                    "AccessKeySecret": access_key_secret,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                print(f"[TTS Token] Response: {json.dumps(data, ensure_ascii=False)}")
                if resp.status == 200 and data.get("Token"):
                    token = data["Token"]["Id"]
                    expire = data["Token"]["ExpireTime"]
                    _token_cache = {"token": token, "expire_time": expire}
                    print(f"[TTS Token] Got token, expires at {expire}")
                    return token
                else:
                    print(f"[TTS Token] Failed: {data}")
                    return ""
    except Exception as e:
        print(f"[TTS Token] Error: {e}")
        traceback.print_exc()
        return ""


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """
    将文字转为语音，返回 MP3 字节流
    使用阿里云语音合成服务
    """
    selected_voice = voice or VOICE
    app_key = settings.ALIYUN_TTS_APP_KEY

    print(f"[TTS] APP_KEY={'SET' if app_key else 'EMPTY'}")

    if not app_key:
        print("[TTS] ALIYUN credentials not configured, using silent fallback")
        return b""

    # 获取 Token
    token = await _get_token()
    if not token:
        print("[TTS] Cannot get token, abort")
        return b""

    print(f"[TTS] Requesting TTS for text: {text[:50]}...")

    # 阿里云 TTS 请求参数（Header 传 Token）
    headers = {
        "Content-Type": "application/json",
        "X-NLS-Token": token,
    }

    payload = {
        "appkey": app_key,
        "text": text,
        "token": token,
        "format": FORMAT,
        "sample_rate": SAMPLE_RATE,
        "voice": selected_voice,
        "volume": 50,
        "speech_rate": 0,
        "pitch_rate": 0,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TTS_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    data = await resp.read()
                    print(f"[TTS] Success: {len(data)} bytes, content-type={content_type}")
                    return data
                else:
                    error_text = await resp.text()
                    print(f"[TTS] Aliyun returned {resp.status}: {error_text}")
                    return b""
    except Exception as e:
        print(f"[TTS] Error type={type(e).__name__}, msg={e}")
        traceback.print_exc()
        return b""
