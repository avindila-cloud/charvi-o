"""Rename 535 orphan valid ke nama expected (strip trailing punct)."""
import os
import glob
import sqlite3
import re
import sys


AUDIO_DIR = "assets/audio_core"
DB_PATH = "charvi_o_data.db"

# Karakter punct Tionghoa yang di-strip di akhir (sama dengan yang dihapus 
# _safe_audio_filename)
TRAILING_PUNCT = r'[\u3000-\u303f\uff00-\uffef\s]+$'


def _get_expected_filenames():
    """Mapping filename -> hanzi dari cache."""
    from services.seed_queue import _safe_audio_filename
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT hanzi FROM cached_translations")
    hanzi_list = [row[0] for row in c.fetchall() if row[0]]
    conn.close()
    return {_safe_audio_filename(h): h for h in hanzi_list}


def find_orphans_to_rename():
    """Cari file orphan yang bisa di-rename (beda cuma trailing punct)."""
    expected_map = _get_expected_filenames()
    all_files = glob.glob(os.path.join(AUDIO_DIR, "*.mp3"))
    
    to_rename = []   # (old_path, new_path, old_name, new_name)
    skipped = []     # (old_name, reason)
    already_match = []
    
    for f in all_files:
        old_name = os.path.basename(f)
        
        # Skip kalau sudah match expected
        if old_name in expected_map:
            already_match.append(old_name)
            continue
        
        # Skip kalau ini bukan .mp3 (harusnya sudah bersih, tapi safety)
        if not old_name.endswith(".mp3"):
            continue
        
        old_base = old_name[:-4]  # remove .mp3
        
        # Strip trailing punct
        stripped = re.sub(TRAILING_PUNCT, '', old_base)
        candidate_name = stripped + ".mp3"
        
        # Cek apakah candidate match dengan expected
        if candidate_name in expected_map:
            new_path = os.path.join(AUDIO_DIR, candidate_name)
            if os.path.exists(new_path):
                skipped.append((old_name, f"target exists: {candidate_name}"))
            else:
                to_rename.append((f, new_path, old_name, candidate_name))
        else:
            skipped.append((old_name, "no match after strip"))
    
    return to_rename, skipped, already_match


def execute_rename():
    to_rename, skipped, already_match = find_orphans_to_rename()
    
    print(f"File yang bisa di-rename: {len(to_rename)}")
    print(f"File yang di-skip: {len(skipped)}")
    print(f"File yang sudah match: {len(already_match)}")
    
    if len(to_rename) == 0:
        print("\nTidak ada file untuk di-rename.")
        return
    
    print("\n=== 5 Contoh rename ===")
    for _, _, old, new in to_rename[:5]:
        print(f"  {old} -> {new}")
    
    print(f"\nMulai rename {len(to_rename)} file...")
    renamed = 0
    failed = 0
    
    for old_path, new_path, old_name, new_name in to_rename:
        try:
            os.rename(old_path, new_path)
            renamed += 1
            if renamed <= 10 or renamed % 50 == 0:
                print(f"  [{renamed}/{len(to_rename)}] {old_name} -> {new_name}")
        except Exception as e:
            failed += 1
            print(f"  ❌ GAGAL: {old_name}: {e}")
    
    print(f"\n✅ Selesai: {renamed} rename, {failed} gagal")
    
    if skipped:
        print(f"\n⚠️ {len(skipped)} di-skip:")
        for name, reason in skipped[:10]:
            print(f"  - {name}: {reason}")


if __name__ == "__main__":
    if "--execute" in sys.argv:
        execute_rename()
    else:
        to_rename, skipped, already_match = find_orphans_to_rename()
        print(f"[DRY-RUN] Akan rename: {len(to_rename)}")
        print(f"[DRY-RUN] Akan skip: {len(skipped)}")
        print(f"[DRY-RUN] Sudah match: {len(already_match)}")
        print(f"[DRY-RUN] Total: {len(to_rename) + len(skipped) + len(already_match)}")
        print("\nJalankan dengan --execute untuk eksekusi")
