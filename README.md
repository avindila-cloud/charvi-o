# 🎙️ Charvi O

**Belajar bahasa Kantonis (Cantonese) praktis untuk pekerja Indonesia (TKW) di Hong Kong.**

Aplikasi perangkat *Streamlit* berbasis paket **services** yang terpisah (STT, terjemahan, TTS, kurikulum, kuis, progress, profil, lisensi). Supabase adalah datastore pusat; *line-of-code* akses langsung ke service tidak ada di UI.

---

## 🚀 Cara jalankan (Fase 1 lokal)

```bash
# 1. Buat env & aktifkan
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Pasang ketergantungan
pip install -r requirements.txt

# 3. Siapkan secrets (hanya lokal)
cp .streamlit/secrets.example .streamlit/secrets.toml   # buat file ini (gitignored)

# 4. Jalankan
streamlit run app.py
```

### Konfigurasi yang diperlukan

- `.env` / `.streamlit/secrets.toml` berisi:
  - `GROQ_API_KEY`, `GEMINI_API_KEY` — untuk STT & terjemahan.
  - `SUPABASE_URL`, `SUPABASE_KEY` / `SUPABASE_SERVICE_KEY` — untuk datastore.
  - `ADMIN_PASSWORD` — untuk halaman admin (opsional).
- Supabase schema: jalankan **manual** di Supabase SQL Editor → New query → Run (lihat `docs/supabase_schema.sql`).

> 🔑 **API key** didapat dari masing-masing penyedia. Jangan pernah commit `.env` / `secrets.toml` — file ini sudah dipasukkan ke `.gitignore`.

---

## 📁 Struktur

```
charvi-o/
├── app.py                    # Halaman utama + state machine + router
├── requirements.txt          # Ketergantungan Python
├── .env.example              # Template rahasia (jangan dicommit)
├── .gitignore
├── README.md
├── docs/
│   └── supabase_schema.sql   # SQL 6 tabel + storage bucket + policy
├── services/                 # Modul pendukung terpisah
│   ├── __init__.py
│   ├── stt.py                # Groq Whisper transcription
│   ├── translate.py          # Google Gemini translation
│   ├── tts.py                # Edge TTS synthesis
│   ├── license.py            # Status lisensi & pembayaran
│   ├── learn.py              # Kurikulum 96 kalimat, 11 kategori
│   ├── quiz.py               # Builder kuis
│   ├── progress.py           # Statistik belajar & kuis
│   ├── profile.py            # Profil & avatar
│   └── ... (db client)
└── assets/
    └── .gitkeep              # Placeholder; taruh logo.png di sini
```

---

## 🧠 Alur state machine

| Status | Tampilkan |
|---|---|
| `new` | Orientasi baru → instruksi bagikan |
| `share_done` | 24 jam gratis → hitung sisa |
| `trial` | Trial berjalan + opsi beli |
| `paywall` | Layar bayar + form paket |
| `active` | Akses penuh (translate, belajar, kuis, progress, profil, admin) |

## 🛠 Troubleshooting

- `ModuleNotFoundError: No module named 'services'` → jalankan `streamlit run app.py` **dari dalam** folder `charvi-o/`.
- Supabase query gagal → cek `SUPABASE_URL` & kunci di secrets.
- TTS/TTS voice tidak ada → pilih suara lain dari `services/tts.VOICES` (id-ID-* / yue-*).

---

> 📋 **Catatan**: `docs/supabase_schema.sql` **hanya file repo** — jalankan manual di Supabase SQL Editor. `assets/` menunggu `logo.png` dari user. PWA & backend FastAPI akan dibuat di fase terpisah (tergantung URL Streamlit).
