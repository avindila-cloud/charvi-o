import sqlite3
import time
import os
import re
import hashlib
from datetime import datetime
from services.translate import translate
from services.tts import synthesize
from services.learn import CURRICULUM
from services.tkw_sentences import TKW_SENTENCES
from services.tkw_sentences_extended import TKW_EXTENDED_SENTENCES
from services.database import save_to_cache
from services.audio_manager import AUDIO_CORE_DIR

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "charvi_o_data.db")

RATE_LIMIT_SECONDS = 6


def _get_conn():
    return sqlite3.connect(DB_PATH)


def build_queue():
    """Siapkan translation_queue baru (P1=CURRICULUM / P2=TKW / P3=kamus)."""
    conn = _get_conn()
    try:
        # Kosongkan tabel antrian
        conn.execute("DELETE FROM translation_queue")
        conn.commit()

        c = conn.cursor()
        c.execute("SELECT indo_text FROM cached_translations")
        cached = {row[0] for row in c.fetchall()}

        pending = []
        # Priority 1: CURRICULUM (Support List & Dict)
        for item in CURRICULUM:
            if isinstance(item, dict):
                indo = item.get("indo") or item.get("id") or item.get("text")
            elif isinstance(item, (tuple, list)):
                indo = item[0]
            else:
                indo = str(item)
            if indo and indo not in cached:
                pending.append((indo, 1))
                cached.add(indo)

        # Priority 2: kalimat umum TKW (~300)
        for kalimat in TKW_SENTENCES:
            if kalimat and kalimat not in cached:
                pending.append((kalimat, 2))
                cached.add(kalimat)

        # Priority 2: TKW EXTENDED SENTENCES (newly added 632+ sentences)
        for kalimat in TKW_EXTENDED_SENTENCES:
            if kalimat and kalimat not in cached:
                pending.append((kalimat, 2))
                cached.add(kalimat)

        # Priority 3: SEMUA kata dari tabel dictionary (CC-Canto)
        c = conn.cursor()
        c.execute("SELECT definisi FROM dictionary WHERE definisi IS NOT NULL AND definisi != ''")
        for (definisi,) in c.fetchall():
            if definisi and definisi not in cached:
                pending.append((definisi, 3))
                cached.add(definisi)

        # Masukkan ke translation_queue
        if pending:
            placeholders = ",".join("(?, ?, 'pending')" for _ in pending)
            params = [item for tup in pending for item in tup[:2]]
            conn.execute(
                f"INSERT OR IGNORE INTO translation_queue (text_indo, priority, status) VALUES {placeholders}",
                params,
            )
            conn.commit()

        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM translation_queue WHERE status = 'pending'")
        count = c.fetchone()[0]

        print(f"[build_queue] Selesai. Total Pending: {count} baris.")
        print(f"[build_queue] - Priority 1 (CURRICULUM): {sum(1 for p in pending if p[1] == 1)}")
        print(f"[build_queue] - Priority 2 (TKW): {sum(1 for p in pending if p[1] == 2)}")
        print(f"[build_queue] - Priority 3 (dictionary): {sum(1 for p in pending if p[1] == 3)}")
        print(f"[build_queue] - Sudah di-cache_translations (skip): {len(cached)}")
    finally:
        conn.close()


def _today_processed_count(conn):
    """Jumlah antrian yang 'done' dan date(processed_at) = today."""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM translation_queue WHERE status='done' AND date(processed_at) = ?",
            (today,),
        )
        return c.fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def process_batch(daily_limit=300):
    """Batch terjemahan harian dengan Gemini + rate-limit safety."""
    conn = _get_conn()
    processed_today = _today_processed_count(conn)
    conn.close()

    if processed_today >= daily_limit:
        print(f"[*] Kuota harian {daily_limit} sudah habis hari ini. Sisa antrian: {daily_limit - processed_today}.")
        return

    remaining = daily_limit - processed_today

    conn = _get_conn()
    try:
        c = conn.cursor()
        items = c.execute(
            "SELECT id, text_indo FROM translation_queue WHERE status='pending' ORDER BY priority ASC, id ASC LIMIT ?",
            (remaining,),
        ).fetchall()
    finally:
        conn.close()

    if not items:
        print("[process_batch] Tidak ada item pending.")
        return

    for idx, (q_id, text_indo) in enumerate(items, 1):
        # f. Cek if cached: jika sudah ada, set langsung 'done' dan continue
        conn = _get_conn()
        try:
            c = conn.cursor()
            c.execute("SELECT 1 FROM cached_translations WHERE indo_text=?", (text_indo,))
            if c.fetchone():
                c.execute(
                    "UPDATE translation_queue SET status='done', processed_at=? WHERE id=?",
                    (datetime.now().isoformat(), q_id),
                )
                conn.commit()
                print(f"[{idx}] Sudah di-cache, skip.")
                continue
        finally:
            conn.close()

        # a. Transaksi 1: tandai processing
        conn = _get_conn()
        try:
            conn.execute("UPDATE translation_queue SET status='processing' WHERE id=?", (q_id,))
            conn.commit()
        finally:
            conn.close()

        try:
            result = translate(text_indo, "id", "yue")
            hanzi = result if isinstance(result, str) else str(result)
            hanzi = hanzi.strip()
            if not hanzi:
                raise RuntimeError("Hasil terjemahan kosong / tidak valid")

            # 3) save_to_cache
            save_to_cache(text_indo, hanzi, "")

            # 4) Tandai done
            conn = _get_conn()
            try:
                conn.execute(
                    "UPDATE translation_queue SET status='done', processed_at=? WHERE id=?",
                    (datetime.now().isoformat(), q_id),
                )
                conn.commit()
            finally:
                conn.close()

            print(f"[{idx}] Translated: {text_indo} -> {hanzi}")

            time.sleep(RATE_LIMIT_SECONDS)  # rate-limit safety

        except Exception as e:
            err = str(e)
            # Hercules: rate-limit / quota
            if any(kw in err.lower() for kw in ["429", "rate limit", "quota", "too many requests"]):
                # Eksponential backoff, lalu hentikan hari ini
                time.sleep(60)
                processed = _today_processed_count(_get_conn())
                print(f"Kuota API hari ini tercapai. Sisa antrian: {daily_limit - processed}. Lanjutkan besok.")
                return

            # c. Error umum — catat, reset ke pending, lanjut ke item berikutnya
            print(f"[{idx}] Error: {err}")
            conn = _get_conn()
            try:
                conn.execute("UPDATE translation_queue SET status='pending' WHERE id=?", (q_id,))
                conn.commit()
            finally:
                conn.close()
            continue

    # c. Setelah loop selesai
    print(f"[process_batch] Selesai. Diproses {len(items)} item.")


def _all_cached_translations(conn):
    """Ambil semua cached_translations yang belum punya file audio."""
    results = []
    c = conn.cursor()
    c.execute("SELECT indo_text, hanzi, jyutping FROM cached_translations")
    for indo_text, hanzi, jyutping in c.fetchall():
        if hanzi and hanzi != "" and not os.path.exists(os.path.join(AUDIO_CORE_DIR, f"{_safe_audio_filename(hanzi)}")):
            results.append((indo_text, hanzi, jyutping))
    return results


def _safe_audio_filename(hanzi: str) -> str:
    """Konversi Hanzi ke nama file yang aman untuk Windows."""
    # Ganti karakter terlarang Windows (< > : " / \ | ? *) dengan underscore
    safe = re.sub(r'[<>:"/\\|?*]', '_', hanzi)
    # Hapus tanda baca Tionghoa yang bisa bermasalah
    safe = re.sub(r'[。，、；：！？「」『』（）]', '_', safe)
    # Bersihkan spasi & titik di awal/akhir
    safe = safe.strip(' ._')
    # Fallback: hash jika hasil kosong atau terlalu panjang
    if len(safe) < 1 or len(safe) > 80:
        safe = 'h_' + hashlib.md5(hanzi.encode('utf-8')).hexdigest()[:12]
    return f"{safe}.mp3"


def generate_audio_batch(daily_limit=300):
    """Sinkronisasi audio dari cached_translations ke assets/audio_core/."""
    conn = _get_conn()
    entries = _all_cached_translations(conn)
    conn.close()

    if not entries:
        print("[generate_audio_batch] Semua cached_translations sudah punya audio.")
        return

    print(f"[generate_audio_batch] Total entri yang butuh audio: {len(entries)}")

    for idx, (indo_text, hanzi, jyutping) in enumerate(entries, 1):
        if idx > daily_limit:
            print(f"[generate_audio_batch] Daily limit {daily_limit} tercapai. Sisa: {len(entries) - idx + 1}.")
            break

        try:
            if not hanzi:
                print(f"[{idx}/{len(entries)}] - (hanzi kosong)")
                continue

            audio_bytes = synthesize(hanzi, "zh-HK-HiuMaanNeural")
            if not audio_bytes:
                print(f"[{idx}/{len(entries)}] - (tidak ada audio yang dihasilkan)")
                continue

            audio_path = os.path.join(AUDIO_CORE_DIR, f"{_safe_audio_filename(hanzi)}")
            os.makedirs(AUDIO_CORE_DIR, exist_ok=True)
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            print(f"[{idx}/{len(entries)}] Audio: {indo_text} -> {hanzi} ({len(audio_bytes)} bytes)")
            time.sleep(1)  # rate-limit: 1 detik/file untuk audio

        except Exception as e:
            print(f"[{idx}/{len(entries)}] Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode in ("build", "build_queue"):
            build_queue()
        elif mode in ("translate", "process"):
            process_batch()
        elif mode in ("audio", "generate_audio"):
            generate_audio_batch()
        else:
            print("Penggunaan: python services/seed_queue.py {build|process|audio}")
            sys.exit(1)
    else:
        print("=== Pre-Warming Cache Bertahap ===")
        print("Mode yang tersedia:")
        print("  python services/seed_queue.py build     -> build translation_queue")
        print("  python services/seed_queue.py process   -> proses terjemahan batch")
        print("  python services/seed_queue.py audio     -> sinkronisasi audio")
