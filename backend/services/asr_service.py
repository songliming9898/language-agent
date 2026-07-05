"""ASR 语音识别服务（Sherpa-ONNX Paraformer 离线方案）"""
import os
import tempfile
import subprocess
import asyncio

# 模型路径
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "sherpa-onnx-paraformer-zh-small")


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


async def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    语音转文字，使用 Sherpa-ONNX Paraformer 离线识别
    """
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    wav_path = None
    try:
        # 先转 wav
        wav_path = _convert_to_wav(tmp_path)
        if not wav_path:
            return ""

        # 检查模型是否存在
        if not os.path.exists(MODEL_DIR):
            print(f"[ASR] Model not found at {MODEL_DIR}, downloading...")
            _download_model()

        if not os.path.exists(MODEL_DIR):
            print("[ASR] Model download failed")
            return ""

        # 使用 sherpa-onnx Python API
        try:
            import sherpa_onnx

            config = sherpa_onnx.OfflineRecognizerConfig(
                model=sherpa_onnx.OfflineModelConfig(
                    paraformer=sherpa_onnx.OfflineParaformerModelConfig(
                        model=os.path.join(MODEL_DIR, "model.int8.onnx"),
                    ),
                    tokens=os.path.join(MODEL_DIR, "tokens.txt"),
                ),
            )
            recognizer = sherpa_onnx.OfflineRecognizer(config)
            import soundfile as sf
            samples, sample_rate = sf.read(wav_path)
            stream = recognizer.create_stream()
            stream.accept_waveform(sample_rate, samples)
            recognizer.decode_stream(stream)
            result = stream.result.text.strip()
            return result
        except ImportError:
            print("[ASR] sherpa-onnx not installed, trying CLI fallback...")
            return await _cli_fallback(wav_path)

    except Exception as e:
        print(f"[ASR] Error: {type(e).__name__}: {e}")
        return ""
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if wav_path and os.path.exists(wav_path):
            os.unlink(wav_path)


async def _cli_fallback(wav_path: str) -> str:
    """使用 sherpa-onnx 命令行工具作为备选"""
    try:
        # 查找 sherpa-onnx 的 CLI 工具
        cmd = [
            "python", "-m", "sherpa_onnx",
            "--tokens", os.path.join(MODEL_DIR, "tokens.txt"),
            "--paraformer-model", os.path.join(MODEL_DIR, "model.int8.onnx"),
            wav_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        text = result.stdout.strip()
        if not text:
            text = result.stderr.strip()
        # 提取识别结果
        for line in text.split("\n"):
            if line.strip() and not line.startswith("[") and not line.startswith("LOG"):
                return line.strip()
        return ""
    except Exception as e:
        print(f"[ASR] CLI fallback error: {e}")
        return ""


def _download_model():
    """下载 Sherpa-ONNX Paraformer 中文小模型"""
    import urllib.request
    import tarfile
    import io

    model_url = (
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
        "asr-models/sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2"
    )
    extract_dir = os.path.dirname(MODEL_DIR)

    print(f"[ASR] Downloading model from {model_url}...")
    try:
        data = urllib.request.urlopen(model_url, timeout=300).read()
        print(f"[ASR] Downloaded {len(data)} bytes, extracting...")
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:bz2") as tar:
            tar.extractall(extract_dir)
        print(f"[ASR] Model extracted to {extract_dir}")
    except Exception as e:
        print(f"[ASR] Download failed: {e}")
