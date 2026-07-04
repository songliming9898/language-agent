"""ASR 语音识别服务"""
import os
import tempfile
import subprocess
import json


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
    语音转文字
    策略：whisper > vosk > 返回空
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

        # 2. 尝试 vosk 离线识别
        try:
            import vosk
            import wave

            wav_path = _convert_to_wav(tmp_path)
            if not wav_path:
                return ""

            # 下载 vosk 小模型（约 40MB）
            model_path = os.path.join(os.path.dirname(__file__), "..", "vosk-model-small-en-us-0.15")
            if not os.path.exists(model_path):
                print("[ASR] vosk model not found, downloading...")
                subprocess.run(
                    ["python", "-c",
                     f"import vosk, urllib.request, zipfile, io, os; "
                     f"url='https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip'; "
                     f"print('Downloading vosk model...'); "
                     f"data=urllib.request.urlopen(url).read(); "
                     f"z=zipfile.ZipFile(io.BytesIO(data)); "
                     f"z.extractall('{os.path.dirname(model_path)}')"],
                    timeout=120,
                )

            if os.path.exists(model_path):
                model = vosk.Model(model_path)
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
        except ImportError:
            print("[ASR] vosk not installed")
        except Exception as e:
            print(f"[ASR] vosk error: {e}")

        return ""
    except Exception as e:
        print(f"[ASR] error: {e}")
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
