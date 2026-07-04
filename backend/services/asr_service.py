"""ASR 语音识别服务"""
import os
import tempfile
import subprocess


async def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    语音转文字
    优先使用 whisper CLI（如果已安装），否则回退到 Google Speech Recognition
    """
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # 优先尝试 whisper
        result = subprocess.run(
            ["whisper", tmp_path, "--model", "tiny", "--language", "en",
             "--output_format", "txt", "--output_dir", os.path.dirname(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        txt_path = os.path.splitext(tmp_path)[0] + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            os.unlink(txt_path)
            if text:
                return text

        # whisper 失败或无输出，回退到 Google Speech Recognition
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="en-US")
            return text
        except ImportError:
            pass
        except Exception:
            pass

        return ""
    except FileNotFoundError:
        # whisper 命令不存在，直接用 Google
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="en-US")
            return text
        except ImportError:
            print("[ASR] speech_recognition not installed, returning empty")
            return ""
        except Exception as e:
            print(f"[ASR] Google recognition error: {e}")
            return ""
    except Exception as e:
        print(f"[ASR] error: {e}")
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
