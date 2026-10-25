"""Progress — statistik belajar dan kuis."""
import os
import streamlit as st
from supabase import create_client

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


def get_progress_map(device_id: str) -> dict:
    """Kembalikan map {phrase_id: record} dari learn_progress."""
    supabase = _get_supabase()
    try:
        resp = supabase.table("learn_progress").select("*").eq("device_id", device_id).execute()
        rows = resp.data or []
    except Exception:
        return {}
    return {r["phrase_id"]: r for r in rows}


def upsert_progress(device_id: str, phrase_id: str, category: str,
                    indo: str, yue: str, jyutping: str, status: str = "learning") -> bool:
    """Insert/ubah satu baris progress."""
    supabase = _get_supabase()
    data = {
        "device_id": device_id,
        "phrase_id": phrase_id,
        "category": category or None,
        "indo": indo or "",
        "yue": yue or "",
        "jyutping": jyutping or "",
        "status": status or "learning",
        "last_seen": "now()",
    }
    try:
        supabase.table("learn_progress").upsert(data).eq("device_id", device_id).eq("phrase_id", phrase_id).execute()
    except Exception:
        return False
    return True


def mark_mastered(device_id: str, phrase_id: str) -> bool:
    """Tandai frasa sebagai dikuasai."""
    return upsert_progress(device_id, phrase_id, None, None, None, None, status="mastered")


def save_quiz_session(device_id: str, category: str, quiz_type: str,
                      total: int, correct: int, score_pct: int) -> bool:
    """Simpan satu sesi kuis."""
    supabase = _get_supabase()
    data = {
        "device_id": device_id,
        "category": category or None,
        "quiz_type": quiz_type or None,
        "total_questions": total,
        "correct_answers": correct,
        "score_pct": score_pct,
        "completed_at": "now()",
    }
    try:
        supabase.table("quiz_sessions").insert(data).execute()
    except Exception:
        return False
    return True


def get_recent_sessions(device_id: str, limit: int = 5) -> list:
    """Kembalikan senarai sesi kuis terbaru."""
    supabase = _get_supabase()
    try:
        resp = supabase.table("quiz_sessions").select("*").eq("device_id", device_id).order("completed_at", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception:
        return []


def get_stats(device_id: str) -> dict:
    """Statistik ringkas: yang dilalui, dikuasai, nilai terakhir."""
    progress = get_progress_map(device_id)
    sessions = get_recent_sessions(device_id, limit=1000)
    stats = {
        "total_learned": len(progress),
        "mastered": sum(1 for r in progress.values() if r.get("status") == "mastered"),
        "total_quiz": len(sessions),
        "recent_score": None,
    }
    if sessions:
        stats["recent_score"] = sessions[0].get("score_pct")
    return stats
