"""Speech-to-text via Whisper (lazy-loaded)."""

import os
import tempfile
import shutil
from typing import Optional

import numpy as np
import sounddevice as sd

try:
    import whisper  # type: ignore
except ImportError:
    whisper = None

MODEL_NAME = os.environ.get("WHISPER_MODEL", "small")
SAMPLE_RATE = 16000

_model = None


def _load_model():
    global _model
    if whisper is None:
        raise ImportError("whisper не установлен. pip install openai-whisper")
    if _model is None:
        _model = whisper.load_model(MODEL_NAME)
    return _model


def _record_audio(duration_sec: float) -> np.ndarray:
    frames = int(duration_sec * SAMPLE_RATE)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    return audio.reshape(-1)


def transcribe_once(timeout_sec: Optional[int] = 10) -> str:
    """Record up to timeout_sec seconds and transcribe with Whisper."""
    if shutil.which("ffmpeg") is None:
        return "ffmpeg не найден в PATH — установите ffmpeg и перезапустите"
    try:
        audio = _record_audio(timeout_sec or 10)
    except Exception as exc:
        return f"Ошибка записи аудио: {exc}"

    try:
        model = _load_model()
    except Exception as exc:
        return f"Ошибка загрузки модели Whisper: {exc}"

    # Convert float32 [-1,1] to int16 WAV bytes
    int16_audio = np.clip(audio, -1.0, 1.0)
    int16_audio = (int16_audio * 32767).astype(np.int16)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()  # close so wave/whisper can reopen on Windows

    import wave

    try:
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # int16
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(int16_audio.tobytes())

        result = model.transcribe(tmp_path, language="ru", fp16=False)
        return result.get("text", "").strip()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass