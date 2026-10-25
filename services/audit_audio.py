"""Audit audio files: verifikasi setiap cached_translation punya file MP3 valid."""
import sqlite3
import os

AUDIO_DIR = "assets/audio_core"

def audit():
    # 1) Ambil semua hanzi dari cache
    conn = sqlite3.connect("charvi_o_data.db")
    c = conn.cursor()
    c.execute("SELECT hanzi FROM cached_translations")
    all_hanzi = [row[0] for row in c.fetchall()]
    conn.close()
    
    print(f"Total cached translations: {len(all_hanzi)}")
    
    # 2) Import safe filename function
    from services.seed_queue import _safe_audio_filename
    
    # 3) Kategorikan setiap entry
    valid = []       # File ada & >5000 bytes
    tiny = []        # File ada tapi <5000 bytes (curiga corrupt)
    missing = []     # File tidak ada sama sekali
    no_audio_dir = not os.path.exists(AUDIO_DIR)
    
    if no_audio_dir:
        print(f"⚠️ Folder {AUDIO_DIR} tidak ada!")
        return
    
    for hanzi in all_hanzi:
        filename = _safe_audio_filename(hanzi)
        filepath = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(filepath):
            missing.append((hanzi, filename))
        else:
            size = os.path.getsize(filepath)
            if size < 5000:
                tiny.append((hanzi, filename, size))
            else:
                valid.append((hanzi, filename, size))
    
    # 4) Laporan
    print(f"\n=== HASIL AUDIT ===")
    print(f"Valid (>=5000 bytes): {len(valid)}")
    print(f"Tiny (<5000 bytes):   {len(tiny)}")
    print(f"Missing (no file):    {len(missing)}")
    
    total_size = sum(s for _, _, s in valid) + sum(s for _, _, s in tiny)
    print(f"Total size on disk:   {total_size / 1024 / 1024:.2f} MB")
    
    # 5) Sample bermasalah
    if tiny:
        print(f"\n=== 10 Contoh TINY (perlu regenerate) ===")
        for hanzi, filename, size in tiny[:10]:
            print(f"  {size:>6} bytes  {filename}")
    
    if missing:
        print(f"\n=== 10 Contoh MISSING (perlu generate) ===")
        for hanzi, filename in missing[:10]:
            print(f"  {filename}")
    
    # 6) Simpan daftar ke file untuk regenerate nanti
    with open("audio_regenerate_list.txt", "w", encoding="utf-8") as f:
        for hanzi, _ in missing:
            f.write(f"{hanzi}\n")
        for hanzi, _, _ in tiny:
            f.write(f"{hanzi}\n")
    
    print(f"\n✅ Daftar regenerate disimpan ke audio_regenerate_list.txt")
    print(f"   Total yang perlu di-regenerate: {len(missing) + len(tiny)}")


if __name__ == "__main__":
    audit()
