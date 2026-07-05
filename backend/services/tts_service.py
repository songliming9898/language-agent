"""TTS 语音合成服务（阿里云语音合成）"""
import io
import hmac
import hashlib
import uuid
import time
import traceback
import urllib.parse
import aiohttp
from config import settings

# 阿里云 TTS 配置
TTS_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts"
VOICE = "zhiyao"        # 儿童英语女声
FORMAT = "mp3"
SAMPLE_RATE = 16000


def _sign_parameters(access_key_id: str, access_key_secret: str) -> dict:
    """生成阿里云语音合成签名参数"""
    timestamp = str(int(time.time()))
    signature_nonce = str(uuid.uuid4())

    # 构建规范化查询字符串
    params = {
        "AccessKeyId": access_key_id,
        "Action": "TextToSpeech",
        "Format": FORMAT,
        "SampleRate": str(SAMPLE_RATE),
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": signature_nonce,
        "SignatureVersion": "1.0",
        "Timestamp": timestamp,
        "Version": "2019-08-23",
        "Voice": VOICE,
    }

    # 按 key 排序
    sorted_params = sorted(params.items())
    query_string = urllib.parse.urlencode(sorted_params)

    # 构建签名字符串
    string_to_sign = f"GET&{urllib.parse.quote_plus('/stream/v1/tts')}&{urllib.parse.quote_plus(query_string, safe='')}"

    # HMAC-SHA1 签名
    signature = hmac.new(
        (access_key_secret + "&").encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()

    import base64
    params["Signature"] = base64.b64encode(signature).decode("utf-8")

    return params


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """
    将文字转为语音，返回 MP3 字节流
    使用阿里云语音合成服务
    """
    selected_voice = voice or VOICE
    access_key_id = settings.ALIYUN_AK_ID
    access_key_secret = settings.ALIYUN_AK_SECRET
    app_key = settings.ALIYUN_TTS_APP_KEY

    print(f"[TTS] AK_ID={access_key_id[:5] if access_key_id else 'EMPTY'}..., "
          f"AK_SECRET={'SET' if access_key_secret else 'EMPTY'}, "
          f"APP_KEY={'SET' if app_key else 'EMPTY'}")

    if not access_key_id or not access_key_secret or not app_key:
        print("[TTS] ALIYUN credentials not configured, using silent fallback")
        return b""

    params = _sign_parameters(access_key_id, access_key_secret)

    # 设置语音参数（覆盖默认值）
    params["Voice"] = selected_voice

    headers = {
        "Content-Type": "application/json",
        "X-NLS-Token": app_key,  # 或者通过 Token 机制
    }

    # 构建完整 URL
    query_string = urllib.parse.urlencode(params)
    url = f"{TTS_URL}?{query_string}"

    payload = {"text": text, "appkey": app_key, "format": FORMAT, "sample_rate": SAMPLE_RATE}

    print(f"[TTS] Requesting Aliyun TTS for text: {text[:50]}...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
