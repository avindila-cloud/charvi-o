"""STT — pengenalan suara lewat Groq Whisper large-v3.

Contoh penggunaan:
    from services.stt import transcribe
    teks = transcribe(audio_bytes, language="id")
"""
import os
from dotenv import load_dotenv
load_dotenv()

try:  # pragma: no cover
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None

_client = None


def _get_client():
    global _client
    if _client is None:
        if Groq is None:
            raise RuntimeError(
                "Package 'groq' belum terinstall. Jalankan: pip install groq"
            )
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY belum diatur.")
        _client = Groq(api_key=api_key)
    return _client


def transcribe(audio_bytes: bytes, language: str = "id") -> str:
    """Transkrip audio (MP3/WAV) menjadi teks.

    Args:
        audio_bytes: data audio mentah dari stt.
        language:    "id" untuk Indonesia, "yue"/"zh" untuk Kantonis.

    Returns:
        Teks yang sudah di-transkrip (dibersihkan spasi/newline).
    """
    if not audio_bytes:
        return ""
    client = _get_client()
    file_payload = {"file": ("audio.mp3", audio_bytes, "audio/mpeg")}
    try:
        resp = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=file_payload,
            language=language if language in ("id", "zh", "yue") else None,
            response_format="text",
        )
    except TypeError:
        # Beberapa versi Groq tidak mendukung `language=None`
        resp = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=file_payload,
            response_format="text",
        )
    text = getattr(resp, "text", None)
    if text is None:
        text = str(resp)
    return str(text).strip()
