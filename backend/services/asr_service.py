"""ASR 语音识别服务（Sherpa-ONNX Paraformer 离线方案 + 全局预加载）"""
import os
import json
import tempfile
import subprocess
import asyncio
import concurrent.futures
import threading

# 全局单例模型
_recognizer = None
_lock = threading.Lock()

# 模型路径（在 backend/models/ 下）
_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "sherpa-onnx-paraformer-zh-small")
_MODEL_FILE = os.path.join(_MODEL_DIR, "model.int8.onnx")
_TOKENS_FILE = os.path.join(_MODEL_DIR, "tokens.txt")


def _get_recognizer():
    """获取全局 Sherpa-ONNX 识别器（懒加载 + 线程安全）"""
    global _recognizer
    if _recognizer is None:
        with _lock:
            if _recognizer is None:
                import sherpa_onnx
                print(f"[ASR] Loading Sherpa-ONNX model from {_MODEL_DIR}...")
                config = sherpa_onnx.OfflineRecognizerConfig(
                    model_config=sherpa_onnx.OfflineModelConfig(
                        paraformer=sherpa_onnx.OfflineParaformerModelConfig(
                            model=_MODEL_FILE,
                        ),
                        tokens=_TOKENS_FILE,
                    ),
                )
                _recognizer = sherpa_onnx.OfflineRecognizer(config)
                print("[ASR] Sherpa-ONNX model loaded (global singleton)")
    return _recognizer


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
        print(f"[ASR] ffmpeg error: {e}")
        return None


def _recognize_sync(wav_path: str) -> str:
    """同步语音识别（在线程池中运行）"""
    import soundfile as sf

    recognizer = _get_recognizer()
    samples, sample_rate = sf.read(wav_path, dtype="float32")
    stream = recognizer.create_stream()
    stream.accept_waveform(sample_rate, samples)
    recognizer.decode_stream(stream)
    result = stream.result.text.strip()
    return result


async def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """语音转文字，使用 Sherpa-ONNX Paraformer 离线识别"""
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    wav_path = None
    try:
        wav_path = _convert_to_wav(tmp_path)
        if not wav_path:
            return ""

        if not os.path.exists(_MODEL_FILE):
            print(f"[ASR] Model not found at {_MODEL_FILE}")
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
