# ============================================================
# SECTION 1: IMPORTS & SETUP
# ============================================================
import urllib.parse
import os
import uuid
from datetime import datetime, timedelta

import streamlit as st

# Environment: .env di root (dev lokal). st.secrets di .streamlit/secrets.toml (Cloud).
from dotenv import load_dotenv

load_dotenv()

from services.license import (PACKAGES, get_user_status, mark_shared,
                              start_trial, create_payment_order, list_orders,
                              direct_activate)
from services.learn import get_all_phrases, LEARN_VOICE
from services.quiz import build_quiz
from services.progress import (get_progress_map, upsert_progress,
                               mark_mastered, save_quiz_session,
                               get_recent_sessions, get_stats)
from services.profile import (get_profile, has_profile, save_profile,
                              upload_avatar)
from services.tts import synthesize
from services.database import (get_cached_translation, save_to_cache,
                               get_dictionary_entry)
from services.audio_manager import get_audio
from services.translate import translate


# ============================================================
# SECTION 2: ADMIN DETECTION
# ============================================================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def is_admin() -> bool:
    """Admin = mengisi password di halaman admin."""
    return st.session_state.get("admin_logged_in", False)


# ============================================================
# SECTION 3: PAYMENT RETURN HANDLER
# ============================================================
def _handle_payment_return() -> None:
    """Baca query params setelah kembali dari Midtrans/backend."""
    qp = st.query_params
    order_id = qp.get("order_id")
    if order_id:
        st.query_params.pop("order_id", None)
        # Hanya aktifkan secara *lokal* untuk Fase 1 (belum ada backend webhook).
        # Pada Fase 2, backend-fastapi -> Supabase -> direct_activate.
        _simulate_success(order_id)


def _simulate_success(order_id: str) -> None:
    """Simulasi selesai bayar: ketik sesuai spesifikasi (jangan pakai kode)."""
    if st.button("Saya sudah lunas — lanjut pakai fisik (simulasi)"):
        st.session_state["order_id"] = None
        order = next((o for o in list_orders(status="pending")
                      if str(o.get("id")) == order_id), None) if order_id else None
        if order:
            device_id = get_device_id()
            pkg = order.get("package_key")
            if pkg and direct_activate(device_id, pkg):
                st.session_state.status = "active"
                st.success(f"Lisensi `{pkg}` diaktifkan. Selamat!")
            else:
                st.error("Gagal mensimulasikan pembayaran. Cek koneksi Supabase.")
        else:
            st.warning("Order tidak ditemukan. Silakan beli ulang.")


# ============================================================
# SECTION 4: DEVICE ID & SESSION STATE
# ============================================================
def get_device_id() -> str:
    """Ambil device_id: prioritas dari PWA query param."""
    # 1) Cek query param pwa_device_id (dari PWA shell)
    pwa_device_id = st.query_params.get("pwa_device_id", "")
    if isinstance(pwa_device_id, list):
        pwa_device_id = pwa_device_id[0] if pwa_device_id else ""
    
    if pwa_device_id and len(pwa_device_id) >= 8:
        st.session_state.device_id = pwa_device_id
        return pwa_device_id
    
    # 2) Fallback: session_state
    if "device_id" not in st.session_state:
        st.session_state.device_id = str(uuid.uuid4())
    return st.session_state.device_id


def get_status() -> str:
    return get_user_status(get_device_id())["status"]


# ============================================================
# SECTION 5: HEADER + LOGO
# ============================================================
def render_header() -> None:
    import os
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=96)
    else:
        st.markdown("<h1 style='font-size: 64px; margin: 0;'>🗣️</h1>", unsafe_allow_html=True)
    st.title("Charvi O")
    st.caption("Belajar bahasa Kantonis praktis — untuk pekerja Indonesia di HK")


# ============================================================
# SECTION 6: STATE MACHINE
# ============================================================
def render_state_banner() -> None:
    status = get_status()
    icon = {"new": "🔑", "share_done": "🤝", "trial": "🔓", "paywall": "🔒", "active": "✅"}[status]
    title = {"new": "Orientasi baru", "share_done": "Dapatkan 24 jam",
             "trial": "TRIAL — beli kunci", "paywall": "Layar bayar yang kamu",
             "active": "Akun aktif, selamat datang!"}[status]
    if status in ("new", "share_done", "trial", "paywall"):
        with st.container(border=True):
            st.info(f"{icon} {title}")
            st.caption({
                "new": "Bagi share dulu biar dapat 24 jam gratis.",
                "share_done": "24 jam kamu tinggal — jalankan perhitungan.",
                "trial": "Trial 24 jam, lalu lanjut beli.",
                "paywall": "Beli paket untuk mengaktifkan akses penuh.",
            }.get(status, ""))


# ============================================================
# SECTION 7: RENDER FUNCTIONS
# ============================================================
def render_payment_form() -> None:
    st.header("Pilih paket")
    with st.form("payment_form"):
        pkg = st.selectbox("Paket", options=sorted(PACKAGES.keys()),
                           format_func=lambda k: PACKAGES[k]["label"])
        buyer_name = st.text_input("Nama pembeli")
        buyer_wa = st.text_input("WhatsApp")
        buyer_email = st.text_input("Email (opsional)")
        submitted = st.form_submit_button("Bayar (simulasi)")
        if submitted:
            if not buyer_name or not buyer_wa:
                st.error("Nama & WhatsApp wajib diisi.")
                return
            oid = create_payment_order(get_device_id(), buyer_name,
                                       buyer_wa, buyer_email, pkg)
            if oid:
                st.success(f"Order dibuat. ID: `{oid}`")
                st.info("Cek WhatsApp untuk rincian pembayaran (Fase 2).")
                st.session_state.order_id = oid
            else:
                st.error("Gagal membuat order. Cek konfigurasi Supabase.")


def render_payment_result() -> None:
    oid = st.session_state.get("order_id")
    if not oid:
        return
    order = next((o for o in list_orders(status="pending")
                  if str(o.get("id")) == oid), None)
    if not order:
        st.session_state.pop("order_id", None)
        return
    status = order.get("status", "pending")
    pkg = order.get("package_key")
    if status == "activated":
        st.success(f"Order `{oid}` aktif. Selamat!")
        st.session_state.pop("order_id", None)
    else:
        st.warning(f"{pkg} — tunggu konfirmasi pembayaran (Fase 2).")
        if st.button("Lanjutkan beli paket lain", key="buy_again"):
            st.session_state.pop("order_id", None)
            st.rerun()


def _render_countdown_component(dt: datetime) -> str:
    if not dt:
        return "−"
    delta = dt - datetime.now()
    total = int(delta.total_seconds())
    if total <= 0:
        return "0:00:00"
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def render_active_license_badge(status: str) -> None:
    map_ = {
        "new": "🔑 Belum bagikan",
        "share_done": "🤝 24 jam gratis berjalan",
        "trial": "🔓 Trial berjalan",
        "paywall": "🔒 Premium dimatikan",
        "active": "✅ Aktif penuh",
    }
    st.caption(map_.get(status, status))


# ============================================================
# SECTION 8: DIALOG (SHOW EXTEND DIALOG)
# ============================================================
@st.dialog("🔄 Perpanjang Akses")
def show_extend_dialog() -> None:
    st.write("Pilih paket perpanjangan Anda di sini.")
    st.write("Pilih berapa lama ingin Anda bertahan.")
    st.write("* 30 hari: 50.000")
    st.write("* 90 hari: 100.000")
    st.write("* 180 hari: 150.000")
    st.write("(Lanjut ke pembayaran pada Fase 2.)")


# ============================================================
# SECTION 9: SIDEBAR PROFILE
# ============================================================
def render_sidebar_profile() -> None:
    st.sidebar.header("Profil")
    if has_profile(get_device_id()):
        prof = get_profile(get_device_id())
        st.sidebar.success(f"Nama: {prof.get('full_name')}")
        st.sidebar.caption(f"Wilayah: {prof.get('city_hk', '-')} · {prof.get('years_in_hk', '-')} th HK")
        if st.sidebar.button("Ubah profil", key="edit_profile"):
            st.session_state["edit_profile_open"] = True
    else:
        st.sidebar.info("Isi profil dulu supaya progress tersimpan.")
        with st.sidebar.form("profile_form"):
            full_name = st.text_input("Nama lengkap", value=st.session_state.get("pf_name", ""))
            nickname = st.text_input("Nickname", value=st.session_state.get("pf_nick", ""))
            whatsapp = st.text_input("WhatsApp")
            email = st.text_input("Email")
            city_hk = st.text_input("Kota HK")
            employer_name = st.text_input("Nama pemberi kerja")
            job_type = st.text_input("Jabatan/jenis pekerjaan")
            years_in_hk = st.number_input("Tahun di HK", min_value=0, max_value=60,
                                          value=st.session_state.get("pf_years", 0))
            bio = st.text_area("Bio", height=60, value=st.session_state.get("pf_bio", ""))
            submitted = st.form_submit_button("Simpan profil")
            if submitted:
                st.session_state.update({
                    "pf_name": full_name, "pf_nick": nickname, "pf_years": years_in_hk,
                    "pf_bio": bio,
                })
                if save_profile(get_device_id(), {
                    "full_name": full_name, "nickname": nickname, "whatsapp": whatsapp,
                    "email": email, "city_hk": city_hk, "employer_name": employer_name,
                    "job_type": job_type, "years_in_hk": years_in_hk, "bio": bio,
                }):
                    st.sidebar.success("Profil disimpan.")
                else:
                    st.sidebar.error("Gagal menyimpan profil.")
    st.sidebar.header("Halaman")
    st.sidebar.page_link("app.py", label="Terjemahkan")
    st.sidebar.page_link("app.py", label="Belajar")
    st.sidebar.page_link("app.py", label="Kuis")
    st.sidebar.page_link("app.py", label="Progress")
    st.sidebar.page_link("app.py", label="Profil")
    st.sidebar.page_link("app.py", label="Admin")


# ============================================================
# SECTION 10: PAGE FUNCTIONS
# ============================================================
def render_translate_page() -> None:
    st.header("Terjemah")
    col_a, col_b = st.columns(2)
    src = col_a.selectbox(
        "Larang asal", ["id", "yue"], index=0, key="translate_source"
    )
    tgt = col_b.selectbox(
        "Larang sasaran", ["yue", "id"], index=1, key="translate_target"
    )
    with st.form("translate_form"):
        text = st.text_area(
            "Teks",
            height=90,
            placeholder="Ketik kalimat Indonesia...",
            key="translate_input",
        )
        submitted = st.form_submit_button("Terjemahkan")

        if submitted and text.strip():
            try:
                with st.spinner("Menerjemahkan..."):
                    # 1. Cek cache lokal DULU (tanpa loading API)
                    cached = get_cached_translation(text.strip())
                    if cached is not None:
                        hanzi = cached["hanzi"]
                        jyutping = cached.get("jyutping", "")
                        st.success(f"🇮🇩 {text}")
                        st.write(f"🇰🇳 {hanzi}")
                        if jyutping:
                            st.caption(f"Jyutping: {jyutping}")
                        _play_audio(hanzi)
                        st.caption("Suara: " + LEARN_VOICE)
                    else:
                        # 2. Cache kosong → panggil API Gemini
                        result = translate(text, src, tgt)
                        hanzi = result
                        # 3. Simpan hasil ke cache lokal
                        save_to_cache(text.strip(), hanzi)
                        st.success(f"🇮🇩 {text}")
                        st.write(f"🇰🇳 {hanzi}")
                        _play_audio(hanzi)
                        st.caption("Suara: " + LEARN_VOICE)
            except Exception as e:
                st.error(f"Gagal menerjemahkan: {e}")


def _play_audio(hanzi: str) -> None:
    """Cek audio lokal dulu; kalau nggak ada, panggil Edge TTS (synthesize)."""
    audio_path = get_audio(hanzi)
    if audio_path and os.path.exists(audio_path):
        st.audio(audio_path)
        st.info("Gunakan suara yang tersimpan.")
    else:
        audio = synthesize(hanzi, voice=LEARN_VOICE)
        if audio:
            st.audio(audio)
            st.info("Sintesis selesai.")


def render_learn_page() -> None:
    st.header("Belajar")
    all_phrases = get_all_phrases()
    categories = ["semua"] + sorted({p["category"] for p in all_phrases})
    cat = st.selectbox("Kategori", categories, index=0, key="learn_category")
    pool = [p for p in all_phrases if (not cat or cat == "semua" or p.get("category") == cat)]
    st.info(f"{len(pool)} frasa tersedia.")

    idx = st.number_input("Frasa ke", min_value=1, max_value=len(pool),
                          value=1, step=1) - 1
    if 0 <= idx < len(pool):
        p = pool[idx]
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(p.get("indo", ""))
        with col2:
            st.subheader(p.get("yue", ""))
        st.caption(p.get("jyutping", ""))

        # --- Kamus lokal (database.py) ---
        st.divider()
        st.subheader("📖 Kamus Lokal")
        dict_text = st.text_input(
            "Cari definisi Hanzi", placeholder="Masukkan Hanzi (misal: 食)",
            key=f"dict_search_{p['id']}"
        )
        if dict_text:
            entry = get_dictionary_entry(dict_text.strip())
            if entry:
                st.success(f"🇰🇳 {entry['hanzi']}")
                st.caption(f"Jyutping: {entry.get('jyutping', '')}")
                st.write(f"📖 {entry.get('definisi', '')}")
            else:
                st.info("Belum ada di database lokal.")

        if st.button("🔊 Dengar", key=f"tts_{p['id']}"):
            try:
                # Cek audio lokal dulu
                audio_path = get_audio(p["yue"])
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path)
                    st.info("Gunakan suara yang tersimpan.")
                else:
                    audio = synthesize(p["yue"], voice=LEARN_VOICE)
                    st.info("Sintesis selesai.")
            except Exception as e:
                st.error(f"TTS gagal: {e}")

        if st.button("✔️ Lakuin", key=f"master_{p['id']}"):
            upsert_progress(get_device_id(), p["id"], p.get("category"),
                            p.get("indo", ""), p.get("yue", ""), p.get("jyutping", ""),
                            status="mastered")
            st.success("Darimana tahu!" if False else "Frasa ditandai dikuasai.")


def render_kamus_terpadu_page() -> None:
    st.header("Kamus Terpadu")
    st.caption("Cari 10.000+ kalimat sehari-hari Kantonis + terjemahan Indonesia.")

    search = st.text_input(
        "Cari kata/kalimat",
        placeholder="Contoh: 食, 食嘅嘢, 洗手間...",
        key="kamus_search"
    )

    if search:
        conn = sqlite3.connect("charvi_o_data.db")
        c = conn.cursor()
        # Cari berdasarkan yue_text atau jyutping
        c.execute("""
            SELECT yue_text, mandarin_text, jyutping, scenario
            FROM canto_daily
            WHERE yue_text LIKE ? OR jyutping LIKE ?
            ORDER BY scenario
            LIMIT 20
        """, (f"%{search}%", f"%{search}%"))
        results = c.fetchall()
        conn.close()

        if results:
            st.subheader(f"🍵 {len(results)} hasil ditemukan")
            for yue, mandarin, jyutping, scenario in results:
                with st.expander(f"🇰🇳 {yue}  |  🇮🇩 {mandarin}  |  {scenario}"):
                    if jyutping:
                        st.caption(f"Jyutping: {jyutping}")
                    if st.button("🔊 Dengar", key=f"kamus_play_{yue[:20]}"):
                        try:
                            audio = synthesize(yue, voice=LEARN_VOICE)
                            if audio:
                                st.audio(audio)
                        except Exception as e:
                            st.error(f"TTS gagal: {e}")
        else:
            st.info("Belum ada hasil. Coba kata lain.")


def render_quiz_page() -> None:
    st.header("Kuis")
    all_phrases = get_all_phrases()
    categories = ["semua"] + sorted({p["category"] for p in all_phrases})
    cat = st.selectbox("Kategori", categories, index=0, key="quiz_category")
    total = st.slider("Soalan", 1, 10, value=5)
    if st.button("🚀 Mulai kuis", key="start_quiz"):
        questions = build_quiz(category=None if cat == "semua" else cat, total=total)
        if not questions:
            st.warning("Tidak ada frasa. Pilih kategori lain.")
        else:
            st.session_state["quiz_qs"] = questions
            st.session_state["quiz_idx"] = 0
            st.session_state["quiz_answers"] = [None] * len(questions)
            st.rerun()

    if "quiz_qs" not in st.session_state:
        st.info("Pilih kategori & mulai kuis.")
        return

    qs = st.session_state["quiz_qs"]
    i = st.session_state.get("quiz_idx", 0)
    if i >= len(qs):
        score = sum(1 for a in st.session_state.get("quiz_answers", [])
                    if a is not None) / len(qs) * 100
        st.subheader("Hasil")
        st.metric("Skor", f"{score:.0f}%")
        if st.button("Ulangi"):
            st.session_state["quiz_idx"] = 0
            st.session_state["quiz_answers"] = [None] * len(qs)
            st.rerun()
        return

    q = qs[i]
    st.subheader(q["indo"])
    st.caption(q.get("jyutping", ""))
    answer = st.radio("Pilihan Kantonis", q["options"], index=0, key=f"q_{i}")
    if st.button("Cek", key=f"check_{i}"):
        st.session_state["quiz_answers"][i] = answer
        st.session_state["quiz_idx"] = i + 1
        st.rerun()


def render_progress_page() -> None:
    st.header("Progress")
    if not has_profile(get_device_id()):
        st.warning("Isi profil dulu (sidebar) agar progress tersimpan.")
        st.stop()
    stats = get_stats(get_device_id())
    st.metric("Kata dilalui", stats["total_learned"])
    st.metric("Dikuasai", stats["mastered"])
    st.metric("Sesi kuis", stats["total_quiz"])
    st.metric("Skor terakhir", f"{stats['recent_score']}%")
    if st.button("Lihat jurnal kuis"):
        for s in get_recent_sessions(get_device_id(), limit=5):
            st.write(f"{s['category']} — {s['score_pct']}% ({s['total_questions']} soal)")
    st.subheader("Frasa yang dilalui")
    progress = get_progress_map(get_device_id())
    for pid, rec in progress.items():
        st.write(f"{pid} — {rec.get('status')}")


def render_profile_page() -> None:
    st.header("Profil")
    if has_profile(get_device_id()):
        prof = get_profile(get_device_id())
        for k, v in prof.items():
            if k != "device_id":
                st.write(f"**{k}**: {v or '-'}")
    else:
        st.info("Belum ada profil. Isi di sidebar")


def render_admin_page() -> None:
    st.header("Admin")
    if not ADMIN_PASSWORD:
        st.info("ADMIN_PASSWORD belum diatur.")
        return
    if not is_admin():
        if st.button("Login admin", key="admin_login_btn"):
            if st.secrets.get("ADMIN_PASSWORD") == st.session_state.get("admin_password", ""):
                st.session_state.admin_logged_in = True
            else:
                st.error("Password salah.")
        st.session_state.admin_password = st.text_input("Password", type="password", key="admin_pwd")
        return
    st.success("Admin log in.")
    for o in list_orders(status="pending"):
        st.write(f"{o.get('package_key')} — {o.get('buyer_name')} — {o.get('status')}")
    st.caption(f"Total order pending: {len(list_orders(status='pending'))}")


# ============================================================
# SECTION 11: ROUTER
# ============================================================
def main():
    st.set_page_config(page_title="Charvi O", layout="wide")

    # --- 1. GERBANG LOGIN GOOGLE ---
    if not st.user.is_logged_in:
        st.title("Selamat Datang di Charvi O")
        st.write("Silakan login dengan akun Google Anda.")
        if st.button("Login dengan Google", type="primary", use_container_width=True):
            st.login("google")
        st.stop()

    # --- 2. SETELAH LOGIN ---
    user_email = st.user.email
    device_id = user_email  # Gunakan email sebagai ID unik

    # Cek status user di database
    access = get_user_status(device_id)
    status = access["status"]

    # Tampilkan notifikasi saat trial sudah aktif
    if st.session_state.get("show_trial_toast", False):
        st.toast("🎉 Akses gratis 24 jam Anda sudah aktif!", icon="✅")
        st.session_state.show_trial_toast = False

    # Jika user baru (belum pernah share/trial)
    if status == "new":
        st.title("Satu Langkah Lagi!")
        st.write("Bagikan Charvi O ke teman Anda untuk mengaktifkan akses gratis 24 jam.")

        share_text = "Coba Charvi O! Penerjemah Kantonis gratis untuk TKW."
        wa_url = f"https://wa.me/?text={urllib.parse.quote(share_text)}"

        # Satu Tombol untuk Share & Aktivasi
        if st.button("📤 Bagikan ke WhatsApp & Aktifkan Trial", type="primary", use_container_width=True):
            # 1. Proses aktivasi di database
            mark_shared(device_id)
            start_trial(device_id)

            # 2. Set flag untuk menampilkan notifikasi setelah rerun
            st.session_state.show_trial_toast = True

            # 3. Buka WhatsApp menggunakan JavaScript
            import streamlit.components.v1 as components
            components.html(f"<script>window.open('{wa_url}', '_blank');</script>", height=0)

            # 4. Refresh halaman agar status berubah jadi 'trial'
            st.rerun()

        st.stop()

    # Jika sedang trial
    elif status == "trial":
        st.success("✅ Akses Trial 24 Jam Aktif!")
        # Lanjut ke render UI utama (panggil _render_all_tabs())

    # Jika trial habis (paywall)
    elif status == "paywall":
        st.warning("Masa trial Anda telah habis. Silakan pilih paket berbayar.")
        render_payment_form()  # Panggil form paket yang sudah ada
        st.stop()

    # --- 3. RENDER APLIKASI UTAMA ---
    # (Biarkan kode untuk memanggil tab, sidebar, dll di bawah sini)


def _render_all_tabs() -> None:
    tab_tool = st.tabs(["translasi", "belajar", "kamus", "kuis", "progress", "profil", "admin"])
    with tab_tool[0]:
        render_translate_page()
    with tab_tool[1]:
        render_learn_page()
    with tab_tool[2]:
        render_kamus_terpadu_page()
    with tab_tool[3]:
        render_quiz_page()
    with tab_tool[4]:
        render_profile_page()
    with tab_tool[5]:
        render_admin_page()


def _render_free_tabs() -> None:
    tab_tool = st.tabs(["translasi", "belajar", "kamus", "kuis"])
    with tab_tool[0]:
        render_translate_page()
    with tab_tool[1]:
        render_learn_page()
    with tab_tool[2]:
        render_kamus_terpadu_page()
    with tab_tool[3]:
        render_quiz_page()


# Run the app
if __name__ == "__main__":
    main()
