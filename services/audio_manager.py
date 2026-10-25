"""Audio Manager: cek file audio lokal → fallback ke Edge TTS.

Alur:
  1. Cari `assets/audio_core/{hanzi}.mp3`
  2. Kalau ada → return path absolut
  3. Kalau nggak ada → return None (app.py nanti panggil synthesize())
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_CORE_DIR = os.path.join(BASE_DIR, "assets", "audio_core")
os.makedirs(AUDIO_CORE_DIR, exist_ok=True)


def get_audio(hanzi: str):
    """Return path absolut kalau file ada, else None."""
    if not hanzi:
        return None
    candidate = os.path.join(AUDIO_CORE_DIR, f"{hanzi}.mp3")
    return candidate if os.path.exists(candidate) else None
