"""TTS 语音合成服务（火山引擎豆包 TTS v3 WebSocket）"""
import json
import struct
import uuid
import asyncio
import websockets
from config import settings


DOUBAO_WS_URL = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"

# WebSocket 二进制协议常量
HEADER_SIZE = 4
FULL_CLIENT_REQUEST = 0b0001
FULL_SERVER_RESPONSE = 0b1001
AUDIO_ONLY_SERVER = 0b1011
AUDIO_ONLY_CLIENT = 0b0011


def _pack_message(msg_type: int, payload: bytes) -> bytes:
    """打包二进制消息：4字节header + payload"""
    header = struct.pack(">I", (msg_type << 28) | (len(payload) & 0x0FFFFFFF))
    return header + payload


def _unpack_message(data: bytes) -> tuple:
    """解包二进制消息，返回 (msg_type, payload)"""
    if len(data) < HEADER_SIZE:
        return None, None
    header = struct.unpack(">I", data[:HEADER_SIZE])[0]
    msg_type = (header >> 28) & 0xF
    payload_len = header & 0x0FFFFFFF
    payload = data[HEADER_SIZE:HEADER_SIZE + payload_len]
    return msg_type, payload


async def text_to_speech(text: str, voice: str = None) -> bytes:
    """
    将文字转为语音，返回 MP3 字节流
    使用火山引擎豆包 TTS v3 WebSocket bidirectional API
    """
    api_key = settings.DOUBAO_ACCESS_TOKEN
    tts_voice = voice or settings.DOUBAO_VOICE

    if not api_key:
        print("[TTS] Doubao API Key not configured")
        return b""

    print(f"[TTS] Doubao synthesizing: {text[:60]}...")

    connect_id = str(uuid.uuid4())

    try:
        async with websockets.connect(
            DOUBAO_WS_URL,
            additional_headers={
                "X-Api-Key": api_key,
                "X-Api-Resource-Id": "volc.tts.default",
                "X-Api-Connect-Id": connect_id,
            },
            max_size=10 * 1024 * 1024,
        ) as ws:
            logid = ws.response.headers.get("x-tt-logid", "")
            print(f"[TTS] Connected, logid={logid}")

            # Step 1: Start connection
            await ws.send(_pack_message(FULL_CLIENT_REQUEST, b""))
            resp = await ws.recv()
            msg_type, _ = _unpack_message(resp)
            if msg_type != FULL_SERVER_RESPONSE:
                print(f"[TTS] Unexpected connection response: type={msg_type}")
                return b""

            # Step 2: Start session
            session_id = str(uuid.uuid4())
            session_req = json.dumps({"event": 1})  # EventType.StartSession = 1
            await ws.send(_pack_message(FULL_CLIENT_REQUEST, session_req.encode()))

            resp = await ws.recv()
            msg_type, payload = _unpack_message(resp)
            if msg_type == FULL_SERVER_RESPONSE and payload:
                session_resp = json.loads(payload.decode())
                if session_resp.get("event") != 2:  # SessionStarted = 2
                    print(f"[TTS] Session start failed: {session_resp}")
                    return b""

            # Step 3: Send text as task request
            task_req = json.dumps({
                "event": 5,  # EventType.TaskRequest = 5
                "req_params": {
                    "speaker": tts_voice,
                    "text": text,
                    "audio_params": {
                        "format": "mp3",
                        "sample_rate": 24000,
                    },
                },
            })
            await ws.send(_pack_message(FULL_CLIENT_REQUEST, task_req.encode()))

            # Step 4: Finish session
            finish_req = json.dumps({"event": 3})  # EventType.FinishSession = 3
            await ws.send(_pack_message(FULL_CLIENT_REQUEST, finish_req.encode()))

            # Step 5: Receive audio data
            audio_data = bytearray()
            while True:
                resp = await ws.recv()
                if isinstance(resp, str):
                    continue
                msg_type, payload = _unpack_message(resp)
                if msg_type == AUDIO_ONLY_SERVER:
                    audio_data.extend(payload)
                elif msg_type == FULL_SERVER_RESPONSE and payload:
                    evt = json.loads(payload.decode())
                    if evt.get("event") == 4:  # SessionFinished = 4
                        break
                    elif evt.get("event") == 6:  # ConnectionFinished = 6
                        break
                else:
                    break

            # Step 6: Finish connection
            await ws.send(_pack_message(FULL_CLIENT_REQUEST, b""))
            try:
                await ws.recv()
            except Exception:
                pass

            if audio_data:
                print(f"[TTS] Success: {len(audio_data)} bytes")
                return bytes(audio_data)
            else:
                print("[TTS] No audio data received")
                return b""

    except Exception as e:
        print(f"[TTS] Error: {type(e).__name__}: {e}")
        return b""
