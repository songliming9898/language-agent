"""ASR 语音识别服务（Vosk 离线方案 + 全局预加载）"""
import os
import json
import tempfile
import subprocess
import asyncio
import concurrent.futures
import threading

# 全局单例模型（启动时加载一次，后续请求复用）
_model = None
_model_lock = threading.Lock()

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "vosk-model-small-en-us-0.15")


def _get_model():
    """获取全局 Vosk 模型（懒加载 + 线程安全）"""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                import vosk
                print(f"[ASR] Loading Vosk model from {MODEL_PATH}...")
                _model = vosk.Model(MODEL_PATH)
                print("[ASR] Vosk model loaded (global singleton)")
    return _model


def _convert_to_wav(input_path: str) -> str | None:
    """用 ffmpeg 将音频转为 16kHz mono WAV"""
    output_path = input_path + ".wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1",
             "-f", "wav", output_path],
            capture_output=True, timeout=15, check=True,
        )
        return output_path
    except Exception as e:
        print(f"[ASR] ffmpeg conversion error: {e}")
        return None


def _recognize_sync(wav_path: str) -> str:
    """同步语音识别（在线程池中运行）"""
    import vosk
    import wave

    model = _get_model()
    wf = wave.open(wav_path, "rb")
    rec = vosk.KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(False)

    result_text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            result_text += res.get("text", "") + " "
    res = json.loads(rec.FinalResult())
    result_text += res.get("text", "")
    wf.close()
    return result_text.strip()


async def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """语音转文字，使用 Vosk 离线识别（全局预加载模型）"""
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    wav_path = None
    try:
        wav_path = _convert_to_wav(tmp_path)
        if not wav_path:
            return ""

        if not os.path.exists(MODEL_PATH):
            print(f"[ASR] Vosk model not found at {MODEL_PATH}")
            return ""

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, _recognize_sync, wav_path)

        return result
    except Exception as e:
        print(f"[ASR] Error: {type(e).__name__}: {e}")
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if wav_path and os.path.exists(wav_path):
            os.unlink(wav_path)
