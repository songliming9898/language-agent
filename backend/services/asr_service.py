"""ASR 语音识别服务"""
import os
import tempfile
import subprocess


def _convert_to_wav(input_path: str) -> str | None:
    """用 ffmpeg 将音频转为 16kHz mono WAV"""
    output_path = input_path + ".wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1",
             "-f", "wav", output_path],
            capture_output=True, timeout=15,
            check=True,
        )
        return output_path
    except Exception as e:
        print(f"[ASR] ffmpeg conversion error: {e}")
        return None


async def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    语音转文字
    优先 whisper CLI，否则用 Google Speech Recognition（需 ffmpeg 转码）
    """
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # 1. 尝试 whisper CLI
        try:
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
        except FileNotFoundError:
            pass

        # 2. 回退：ffmpeg 转 WAV → Google Speech Recognition
        wav_path = _convert_to_wav(tmp_path)
        if not wav_path:
            return ""

        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="en-US")
            return text
        except ImportError:
            print("[ASR] speech_recognition not installed")
            return ""
        except Exception as e:
            print(f"[ASR] Google recognition error: {e}")
            return ""
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)

        return ""
    except Exception as e:
        print(f"[ASR] error: {e}")
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
