# Fase 2 — Midtrans Backend (`midtrans_backend/`)

## Latar Belakang
Fase 1 (UI Streamlit + `services/` Python: STT, terjemahan, TTS, license, kuis, progress, profil) sudah selesai, termasuk `.env` (KEY=value), Streamlit di `localhost:8502`, dan validasi struktur (11/11 render, 6/6 license fungsi). Fase 2 menutup sirkuit beli: **Midtrans payment backend** yang mengubah tombol beli → pembayaran → license code.

## Tujuan
1. Buat folder `midtrans_backend/` berbasis **FastAPI + Uvicorn** di HERMES VENV.
2. File utama: `main.py` dengan endpoint berikut:
   - `POST /pay` — terima `{device_id, package_key, buyer_name, buyer_wa, buyer_email}`. CKan order Midtrans Snap, sisip baris `payment_orders` (status=pending), return:
     ```json
     {"order_id": "...", "transaction_status": "pending", "order_value": 50000, "item_title": "Aktif 90 Hari", "expires_in": 10}
     ```
     `app.py` me-render form pembayaran pakai Snap iframe + client key.
   - `POST /notification` — callback Midtrans. Jika `transaction_status=capture` (berhasil), update `payment_orders` (→ paid, paid_at=now, license_code=60 karakter alfanumerik acak), insert baris `licenses` (device_id, active_until=N hari, shared=false). Return `200`.
   - `GET /status/{order_id}` — status order + detail pembayaran (dipakai `list_orders` admin).
3. Lingkungan: `MIDTRANS_SERVER_KEY`, `MIDTRANS_CLIENT_KEY`, `ADMIN_PASSWORD`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ADMIN_SECRET_TOKEN` (key `lic_code` dari `licenses`).
4. `packages.json`-setara paket: `30_hari` (50.000/30 hari), `90_hari` (100.000/90 hari), `180_hari` (150.000/180 hari) — nilai sesuai `docs/supabase_schema.sql` (PACKAGES).
5. Code lisensi: 60 karakter alfanumerik, diambil dari `payment_orders.license_code`.
6. Admin (opsional): `GET /admin/orders` (list payment_orders), `POST /admin/activate` (direct_activate) — set status=paid + license_code. Ganti `ADMIN_SECRET_TOKEN` (require header).

## Kriteria Verifikasi Fase 2
- `pip install -r requirements.txt` di HERMES VENV; impor bersih.
- `uvicorn midtrans_backend.main:app --port 8000` start; `curl -X POST /pay` (device_id sembarang) balas payload Snap; `curl -X POST /notification` dari capture test callback balas 200.
- `.env` bersih: `KEY=value` (tanpa spasi, tanpa kutip), key Midtrans + Supabase placeholder.
- `services/license.py` & `app.py`: pola `activate_license_with_code`/`license_code` belum dihapus di Fase 1 tetap bersih (tidak dicampur ke Fase 2).
- **Bukan bagian Fase 2**: eksekusi `docs/supabase_schema.sql` di Supabase SQL Editor (hanya user yang punya project Supabase); flow API STT/Gemini/Groq masih butuh kunci live.

## Output Fase 2 yang diharapkan
- `midtrans_backend/main.py`, `midtrans_backend/requirements.txt`, `midtrans_backend/.env.example`, `midtrans_backend/README.md`.
- Sinkronisasi dengan `services/license.py` (create_payment_order/list_orders/direct_activate) dan `app.py` (render form + notification handler).
