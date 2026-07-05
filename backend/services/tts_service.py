"""TTS 语音合成服务（腾讯云 TTS）"""
import json
import base64
import uuid
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tts.v20190823 import tts_client, models
from config import settings


def text_to_speech_sync(text: str, voice_type: int = None, language: int = None) -> bytes:
    """
    将文字转为语音，返回 MP3 字节流（同步版本，供 async 包装调用）
    使用腾讯云基础语音合成 TextToVoice API
    """
    secret_id = settings.TENCENT_SECRET_ID
    secret_key = settings.TENCENT_SECRET_KEY
    tts_voice = voice_type or settings.TTS_VOICE_TYPE
    tts_language = language or settings.TTS_PRIMARY_LANGUAGE

    if not secret_id or not secret_key:
        print("[TTS] Tencent Cloud SecretId/SecretKey not configured")
        return b""

    print(f"[TTS] Tencent TTS synthesizing: {text[:60]}... (voice={tts_voice})")

    try:
        cred = credential.Credential(secret_id, secret_key)

        http_profile = HttpProfile()
        http_profile.endpoint = "tts.tencentcloudapi.com"

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        client = tts_client.TtsClient(cred, "ap-guangzhou", client_profile)

        req = models.TextToVoiceRequest()
        params = {
            "Text": text,
            "SessionId": str(uuid.uuid4()),
            "VoiceType": tts_voice,
            "PrimaryLanguage": tts_language,
            "Codec": "mp3",
            "SampleRate": 16000,
            "Speed": 0,
            "Volume": 0,
            "ModelType": 1,
            "ProjectId": 0,
        }
        req.from_json_string(json.dumps(params))

        resp = client.TextToVoice(req)

        audio_b64 = resp.Audio
        if not audio_b64:
            print("[TTS] Empty audio response")
            return b""

        audio_data = base64.b64decode(audio_b64)
        print(f"[TTS] Success: {len(audio_data)} bytes, request_id={resp.RequestId}")
        return audio_data

    except Exception as e:
        print(f"[TTS] Error: {type(e).__name__}: {e}")
        return b""


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """
    异步接口，内部调用同步方法
    voice 参数保留兼容，实际使用 config 中的 TTS_VOICE_TYPE
    """
    import asyncio
    return await asyncio.to_thread(text_to_speech_sync, text)
