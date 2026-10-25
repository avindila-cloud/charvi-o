"""TTS — sintesis suara lewat Edge TTS (gratis, tanpa API key).

Voice Kantonis & Indonesia yang valid (per dokumentasi Microsoft Edge TTS).
"""
import asyncio
from edge_tts import Communicate

# Voice yang VALID di Edge TTS (jangan ganti nama!)
VOICES = {
    "id": [
        ("id-ID-GadisNeural", "Gadis (Perempuan)"),
        ("id-ID-ArdiNeural",  "Ardi (Laki-laki)"),
    ],
    "yue": [
        ("zh-HK-HiuMaanNeural", "HiuMaan (Kantonis - Perempuan)"),
        ("zh-HK-WanLungNeural", "WanLung (Kantonis - Laki-laki)"),
        ("zh-HK-HiuGaaiNeural", "HiuGaai (Kantonis - Perempuan muda)"),
    ],
}

# Voice default untuk Kantonis (dipakai di generate_audio_batch)
DEFAULT_YUE_VOICE = "zh-HK-HiuMaanNeural"


async def _synthesize_async(text: str, voice: str) -> bytes:
    """Internal: sintesis async."""
    communicate = Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


def synthesize(text: str, voice_code: str = None, voice: str = None) -> bytes:
    """Sintesis teks ke MP3 via Edge TTS.
    
    Menerima `voice_code=` atau `voice=` (untuk kompatibilitas).
    """
    if not text or not text.strip():
        return b""
    
    # Terima kedua nama parameter
    vc = voice_code or voice or DEFAULT_YUE_VOICE
    
    try:
        return asyncio.run(_synthesize_async(text.strip(), vc.strip()))
    except Exception as e:
        print(f"❌ TTS error ({vc}): {e}")
        return b""