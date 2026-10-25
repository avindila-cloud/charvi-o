"""Profile — data pengguna dan avatar."""
import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from supabase import create_client
import time

_TAB = "_supabase_client"


def _get_supabase():
    """Ambil client Supabase dari env atau st.secrets."""
    global _TAB
    if _TAB:
        return _TAB
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or st.secrets.get("SUPABASE_SERVICE_KEY")
        or st.secrets.get("SUPABASE_PUBLISHABLE_KEY")
    )
    if not url:
        raise RuntimeError(
            "SUPABASE_URL belum diatur. Isi di .streamlit/secrets.toml atau lingkungan."
        )
    _TAB = create_client(url, key)
    return _TAB


def get_profile(device_id: str) -> dict:
    """Kembalikan baris user_profiles untuk device_id (kosong jika tidak ada)."""
    supabase = _get_supabase()
    try:
        resp = supabase.table("user_profiles").select("*").eq("device_id", device_id).execute()
        row = resp.data[0] if resp.data else None
    except Exception:
        return {}
    return row or {}


def has_profile(device_id: str) -> bool:
    """Benar jika user sudah punya profil lengkap (ada full_name)."""
    prof = get_profile(device_id)
    return bool(prof.get("full_name") and prof.get("full_name").strip())


def save_profile(device_id: str, data: dict) -> bool:
    """Upsert profil pengguna."""
    supabase = _get_supabase()
    record = {
        "device_id": device_id,
        "full_name": data.get("full_name", "").strip(),
        "nickname": data.get("nickname", "").strip() or None,
        "whatsapp": data.get("whatsapp", "").strip(),
        "email": data.get("email", "").strip() or None,
        "city_hk": data.get("city_hk", None),
        "employer_name": data.get("employer_name", "").strip() or None,
        "job_type": data.get("job_type", None),
        "years_in_hk": data.get("years_in_hk", 0) or None,
        "bio": data.get("bio", "").strip() or None,
    }
    try:
        supabase.table("user_profiles").upsert(record).eq("device_id", device_id).execute()
    except Exception:
        return False
    return True


def upload_avatar(device_id: str, file_bytes, content_type: str = "image/png") -> str:
    """Upload avatar ke bucket storage 'avatars' dan kembalikan URL publik."""
    supabase = _get_supabase()
    ext = "png"
    if content_type == "image/jpeg":
        ext = "jpg"
    elif content_type == "image/gif":
        ext = "gif"
    filename = f"{device_id[:8]}_{int(time.time() * 1000)}.{ext}"
    try:
        supabase.storage.from_("avatars").upload(filename, file_bytes, {"content-type": content_type})
        url = supabase.storage.from_("avatars").get_public_url(filename)
    except Exception:
        return ""
    return url or ""
