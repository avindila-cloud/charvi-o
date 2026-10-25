"""Execute Tahap 2: rename 333 orphan + delete 217 duplicate."""
import os
import glob
import sqlite3
import re


AUDIO_DIR = "assets/audio_core"
DB_PATH = "charvi_o_data.db"
TRAILING_PUNCT = r'[\u3000-\u303f\uff00-\uffef\s]+$'


def _get_expected_filenames():
    from services.seed_queue import _safe_audio_filename
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT hanzi FROM cached_translations")
    hanzi_list = [row[0] for row in c.fetchall() if row[0]]
    conn.close()
    return {_safe_audio_filename(h): h for h in hanzi_list}


def categorize():
    expected_map = _get_expected_filenames()
    all_files = glob.glob(os.path.join(AUDIO_DIR, "*.mp3"))
    
    to_rename = []
    duplicates = []
    no_match = []
    already_match = []
    
    for f in all_files:
        old_name = os.path.basename(f)
        
        if old_name in expected_map:
            already_match.append(f)
            continue
        
        if not old_name.endswith(".mp3"):
            continue
        
        old_base = old_name[:-4]
        stripped = re.sub(TRAILING_PUNCT, '', old_base)
        candidate_name = stripped + ".mp3"
        
        if candidate_name in expected_map:
            new_path = os.path.join(AUDIO_DIR, candidate_name)
            if os.path.exists(new_path):
                # DUPLIKAT - target sudah ada
                duplicates.append((f, new_path))
            else:
                # Bisa rename
                to_rename.append((f, new_path))
        else:
            no_match.append(f)
    
    return already_match, to_rename, duplicates, no_match


def execute():
    already_match, to_rename, duplicates, no_match = categorize()
    
    print(f"=== SEBELUM EKSEKUSI ===")
    print(f"Total file: {len(already_match) + len(to_rename) + len(duplicates) + len(no_match)}")
    print(f"Sudah match: {len(already_match)}")
    print(f"Akan rename: {len(to_rename)}")
    print(f"Duplikat (akan dihapus): {len(duplicates)}")
    print(f"No match: {len(no_match)}")
    
    # === RENAME 333 ===
    print(f"\n=== RENAME {len(to_rename)} FILE ===")
    renamed = 0
    rename_failed = 0
    for old_path, new_path in to_rename:
        try:
            os.rename(old_path, new_path)
            renamed += 1
            if renamed <= 5 or renamed % 50 == 0:
                print(f"  [{renamed}/{len(to_rename)}] {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
        except Exception as e:
            rename_failed += 1
            print(f"  ❌ GAGAL rename: {os.path.basename(old_path)}: {e}")
    
    print(f"\n✅ Rename: {renamed} berhasil, {rename_failed} gagal")
    
    # === HAPUS 217 DUPLIKAT ===
    print(f"\n=== HAPUS {len(duplicates)} DUPLIKAT ===")
    deleted = 0
    delete_failed = 0
    for dup_path, target_path in duplicates:
        try:
            os.remove(dup_path)
            deleted += 1
            if deleted <= 5 or deleted % 50 == 0:
                print(f"  [{deleted}/{len(duplicates)}] Hapus: {os.path.basename(dup_path)}")
        except Exception as e:
            delete_failed += 1
            print(f"  ❌ GAGAL hapus: {os.path.basename(dup_path)}: {e}")
    
    print(f"\n✅ Hapus: {deleted} berhasil, {delete_failed} gagal")
    
    # === FINAL STATE ===
    remaining = glob.glob(os.path.join(AUDIO_DIR, "*.mp3"))
    print(f"\n=== SESUDAH EKSEKUSI ===")
    print(f"Total file: {len(remaining)}")
    print(f"Match cache: {len(already_match) + renamed}")
    print(f"No match sisa: {len(no_match)}")
    if no_match:
        print(f"\n⚠️ 1 file no-match yang perlu investigasi:")
        for f in no_match:
            print(f"  {os.path.basename(f)}")


if __name__ == "__main__":
    execute()
