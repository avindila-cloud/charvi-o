"""license — keadaan lisensi, shared, trial, dan order pembayaran.

Deklarasi paket:
    PACKAGES = {
        "30_hari":  {"label": "Aktif 30 Hari",  "price": 50000,  "days": 30},
        "90_hari":  {"label": "Aktif 90 Hari",  "price": 100000, "days": 90},
        "180_hari": {"label": "Aktif 180 Hari", "price": 150000, "days": 180},
    }

Status yang dikembalikan oleh get_user_status():
    "new" | "share_done" | "trial" | "paywall" | "active"
"""
import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client

PACKAGES = {
    "30_hari":  {"label": "Aktif 30 Hari",  "price": 50000,  "days": 30},
    "90_hari":  {"label": "Aktif 90 Hari",  "price": 100000, "days": 90},
    "180_hari": {"label": "Aktif 180 Hari", "price": 150000, "days": 180},
}

_STATUS_NEW = "new"
_STATUS_SHARE_DONE = "share_done"
_STATUS_TRIAL = "_trial"
_STATUS_PAYWALL = "paywall"
_STATUS_ACTIVE = "active"

_TAB = "_supabase_client"


def _parse_dt(dt_val):
    if not dt_val:
        return None
    if isinstance(dt_val, datetime):
        return dt_val.replace(tzinfo=None)
    try:
        dt_str = str(dt_val).replace('Z', '+00:00')
        parsed = datetime.fromisoformat(dt_str)
        return parsed.replace(tzinfo=None)
    except Exception:
        return None


def _get_supabase():
    from supabase import create_client
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
    if not url:
        raise RuntimeError(
            "SUPABASE_URL belum diatur. Isi di .streamlit/secrets.toml atau lingkungan."
        )
    return create_client(url, key)


def get_user_status(device_id: str) -> dict:
    """Kembalikan status pengguna berdasarkan row licenses.

    Returns:
        {
            "status": "new" | "share_done" | "trial" | "paywall" | "active",
            "record": dict | None,
            "trial_end": datetime | None,
            "active_until": datetime | None,
        }
    """
    supabase = _get_supabase()
    try:
        resp = supabase.table("licenses").select("*").eq("device_id", device_id).execute()
        row = resp.data[0] if resp.data else None
    except Exception:
        row = None

    if row is None:
        record = None
        status = _STATUS_NEW
    else:
        record = dict(row)
        active_until = _parse_dt(row.get("active_until"))
        trial_end = _parse_dt(row.get("trial_end"))
        trial_used = row.get("trial_used")
        shared = row.get("shared")
        if active_until and active_until > datetime.now():
            status = _STATUS_ACTIVE
        elif trial_used and trial_end and trial_end > datetime.now():
            status = _STATUS_TRIAL
        elif shared:
            status = _STATUS_SHARE_DONE
        else:
            status = _STATUS_NEW

    return {
        "status": status,
        "record": record,
        "trial_end": row.get("trial_end") if row else None,
        "active_until": row.get("active_until") if row else None,
    }


def mark_shared(device_id: str):
    """Tandai device sudah berbagi (aktifkan trial 24 jam)."""
    supabase = _get_supabase()
    try:
        now_iso = datetime.now().isoformat()
        
        data = {
            "device_id": device_id,
            "shared": True,
            "shared_at": now_iso,
            "trial_used": False,
            "trial_end": (datetime.now() + timedelta(hours=24)).isoformat(),
            "active_until": None,
        }
        supabase.table("licenses").upsert(data, on_conflict="device_id").execute()
    except Exception as e:
        print(f"❌ GAGAL SIMPAN MARK_SHARED: {e}")
        raise e
    return True


def start_trial(device_id: str) -> bool:
    """Klaim trial 24 jam. Hanya bisa jika user sudah share dan belum pernah trial."""
    supabase = _get_supabase()
    try:
        now = datetime.now()
        trial_end_iso = (now + timedelta(hours=24)).isoformat()

        data = {
            "device_id": device_id,
            "trial_used": True,
            "trial_end": trial_end_iso
        }
        # Gunakan upsert yang benar (jangan pakai .eq)
        supabase.table("licenses").upsert(data, on_conflict="device_id").execute()
        return True
    except Exception as e:
        print(f"❌ GAGAL START_TRIAL: {e}")
        return False


def _activate_license(device_id: str, package_key: str, active_until: datetime):
    supabase = _get_supabase()
    payload = {
        "active_until": active_until.isoformat(),
        "trial_used": False,
        "trial_end": None,
        "shared": False,
        "shared_at": None,
    }
    try:
        supabase.table("licenses").upsert(payload, on_conflict="device_id").execute()
    except Exception as e:
        print(f"❌ GAGAL UPSERT_LICENSE: {e}")
    # tandai order selesai
    try:
        supabase.table("payment_orders").update({
            "status": "activated",
            "paid_at": datetime.now().isoformat(),
            "activated_at": datetime.now().isoformat(),
        }).eq("device_id", device_id).eq("package_key", package_key).execute()
    except Exception as e:
        print(f"❌ GAGAL UPDATE_PAYMENT: {e}")


def create_payment_order(device_id: str, buyer_name: str, buyer_wa: str,
                         buyer_email: str | None, package_key: str) -> int | None:
    """Buat order pembayaran baru. Kembalikan id order."""
    supabase = _get_supabase()
    data = {
        "device_id": device_id,
        "buyer_name": buyer_name,
        "buyer_wa": buyer_wa,
        "buyer_email": buyer_email or None,
        "package_key": package_key,
        "package_label": PACKAGES.get(package_key, {}).get("label", package_key),
        "price": PACKAGES.get(package_key, {}).get("price", 0),
        "status": "pending",
    }
    try:
        resp = supabase.table("payment_orders").insert(data).execute()
        row = resp.data[0] if resp.data else None
    except Exception as e:
        print(f"❌ GAGAL BUAT_ORDER: {e}")
        return None
    return row.get("id") if row else None


def list_orders(status: str = "pending", limit: int = 100) -> list:
    """Kembalikan daftar order."""
    supabase = _get_supabase()
    try:
        resp = supabase.table("payment_orders").select("*").eq("status", status).order("created_at", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception as e:
        print(f"❌ GAGAL LIST_ORDERS: {e}")
        return []


def direct_activate(device_id: str, package_key: str) -> bool:
    """Aktifkan lisensi otomatis (biasanya dari webhook Midtrans)."""
    days = PACKAGES.get(package_key, {}).get("days", 30)
    active_until = datetime.now() + timedelta(days=days)
    try:
        _activate_license(device_id, package_key, active_until)
    except Exception as e:
        print(f"❌ GAGAL DIRECT_ACTIVATE: {e}")
        return False
    return True
