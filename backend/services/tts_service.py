"""TTS 语音合成服务（阿里云语音合成）"""
import json
import time
import uuid
import hmac
import hashlib
import base64
import traceback
import urllib.parse
import aiohttp
from config import settings

# 阿里云 Token 换取地址
TOKEN_URL = "https://nls-meta.cn-shanghai.aliyuncs.com/pop/2018-05-18/tokens"
# 语音合成地址
TTS_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts"

VOICE = "zhiyao"
FORMAT = "mp3"
SAMPLE_RATE = 16000

# Token 缓存
_token_cache = {"token": "", "expire_time": 0}


def _sign_request(access_key_id: str, access_key_secret: str) -> str:
    """生成阿里云 POP API 签名，返回签名字符串"""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    signature_nonce = str(uuid.uuid4())

    # 请求参数
    params = {
        "AccessKeyId": access_key_id,
        "Action": "CreateToken",
        "Format": "JSON",
        "RegionId": "cn-shanghai",
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": signature_nonce,
        "SignatureVersion": "1.0",
        "Timestamp": timestamp,
        "Version": "2018-05-18",
    }

    # 排序并构造规范化查询字符串
    sorted_params = sorted(params.items())
    query_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)

    # 构造待签名字符串
    string_to_sign = (
        "GET" + "&"
        + urllib.parse.quote_plus("/") + "&"
        + urllib.parse.quote_plus(query_string, safe="")
    )

    # HMAC-SHA1 签名
    h = hmac.new(
        (access_key_secret + "&").encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    )
    signature = base64.b64encode(h.digest()).decode("utf-8")

    return f"{query_string}&Signature={urllib.parse.quote(signature, safe='')}"


async def _get_token() -> str:
    """获取阿里云语音合成 Token（带缓存）"""
    global _token_cache

    if _token_cache["token"] and time.time() < _token_cache["expire_time"] - 60:
        return _token_cache["token"]

    access_key_id = settings.ALIYUN_AK_ID
    access_key_secret = settings.ALIYUN_AK_SECRET

    if not access_key_id or not access_key_secret:
        print("[TTS Token] AK not configured")
        return ""

    signed_query = _sign_request(access_key_id, access_key_secret)
    url = f"{TOKEN_URL}?{signed_query}"

    print(f"[TTS Token] Requesting new token...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                text = await resp.text()
                print(f"[TTS Token] Status={resp.status}, body={text[:300]}")
                if resp.status == 200:
                    data = json.loads(text)
                    if "Token" in data and "Id" in data["Token"]:
                        token = data["Token"]["Id"]
                        expire = data["Token"]["ExpireTime"]
                        _token_cache = {"token": token, "expire_time": expire}
                        print(f"[TTS Token] Got token, expires at {expire}")
                        return token
                    else:
                        print(f"[TTS Token] Unexpected response: {data}")
                        return ""
                else:
                    return ""
    except Exception as e:
        print(f"[TTS Token] Error: {e}")
        traceback.print_exc()
        return ""


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """将文字转为语音，返回 MP3 字节流"""
    selected_voice = voice or VOICE
    app_key = settings.ALIYUN_TTS_APP_KEY

    print(f"[TTS] APP_KEY={'SET' if app_key else 'EMPTY'}")

    if not app_key:
        print("[TTS] No APP_KEY configured, skip")
        return b""

    token = await _get_token()
    if not token:
        print("[TTS] Cannot get token, abort")
        return b""

    print(f"[TTS] Requesting TTS for: {text[:50]}...")

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
                    print(f"[TTS] Success: {len(data)} bytes, type={content_type}")
                    return data
                else:
                    error_text = await resp.text()
                    print(f"[TTS] Aliyun returned {resp.status}: {error_text}")
                    return b""
    except Exception as e:
        print(f"[TTS] Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return b""
