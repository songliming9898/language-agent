"""ASR 语音识别服务（Demo 阶段使用 Whisper 本地模型）"""
import os
import tempfile
import subprocess


async def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    语音转文字
    Demo阶段：使用 openai-whisper 命令行（需安装 whisper）
    后续可切换为腾讯云 ASR
    """
    # 写入临时文件
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # 使用 whisper CLI
        result = subprocess.run(
            [
                "whisper",
                tmp_path,
                "--model", "tiny",
                "--language", "en",
                "--output_format", "txt",
                "--output_dir", os.path.dirname(tmp_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # 读取识别结果
        txt_path = os.path.splitext(tmp_path)[0] + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            os.unlink(txt_path)
            return text
        return ""
    except Exception:
        # Whisper 不可用时返回空（前端会提示）
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
