"""Cleanup file audio sampah + orphan setelah fix bugs.

Kategori sampah yang dihapus:
1. Double extension: {name}.mp3.mp3
2. Comma Tionghoa di nama: 多謝呀，先生.mp3
3. Slash di nama (jika ada): 先生/女士.mp3
4. Orphan: file MP3 yang namanya TIDAK ada di cache (_safe_audio_filename)

Mode: DRY-RUN dulu (tidak hapus), lalu konfirmasi, baru hapus.
"""
import os
import glob
import sqlite3


AUDIO_DIR = "assets/audio_core"
DB_PATH = "charvi_o_data.db"


def _get_expected_filenames():
    """Ambil semua filename yang seharusnya ada (dari cache)."""
    from services.seed_queue import _safe_audio_filename

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT hanzi FROM cached_translations")
    hanzi_list = [row[0] for row in c.fetchall() if row[0]]
    conn.close()

    expected = set()
    for hanzi in hanzi_list:
        expected.add(_safe_audio_filename(hanzi))
    return expected


def cleanup(dry_run=True):
    if not os.path.exists(AUDIO_DIR):
        print(f"Folder {AUDIO_DIR} tidak ada")
        return

    all_files = glob.glob(os.path.join(AUDIO_DIR, "*"))
    expected_filenames = _get_expected_filenames()

    print(f"Mode: {'DRY-RUN (tidak hapus)' if dry_run else 'HAPUS'}")
    print(f"Total file di disk: {len(all_files)}")
    print(f"File yang diharapkan (dari cache): {len(expected_filenames)}")

    double_ext = []
    comma_in_name = []
    slash_in_name = []
    non_mp3 = []
    orphan = []

    for f in all_files:
        name = os.path.basename(f)
        if name.endswith(".mp3.mp3"):
            double_ext.append(f)
        elif "/" in name or "\\" in name:
            slash_in_name.append(f)
        elif "\uff0c" in name:
            comma_in_name.append(f)
        elif not name.endswith(".mp3"):
            non_mp3.append(f)
        elif name not in expected_filenames:
            orphan.append(f)

    print("\n=== Kategori File ===")
    print(f"1. .mp3.mp3 (double ext):     {len(double_ext)}")
    print(f"2. Comma Tionghoa di nama:    {len(comma_in_name)}")
    print(f"3. Slash di nama:              {len(slash_in_name)}")
    print(f"4. Non-mp3:                    {len(non_mp3)}")
    print(f"5. Orphan (nama tidak match):  {len(orphan)}")

    total = len(double_ext) + len(comma_in_name) + len(slash_in_name) + len(non_mp3) + len(orphan)
    print(f"\nTotal yang akan dihapus: {total}")

    if len(orphan) > 0:
        print("\n=== 10 Contoh ORPHAN ===")
        for f in orphan[:10]:
            print(f"  {os.path.basename(f)}")

    if dry_run:
        print("\n[MODE DRY-RUN] Tidak ada yang dihapus. Jalankan dengan --delete untuk eksekusi.")
        return

    deleted = 0
    for f in double_ext + comma_in_name + slash_in_name + non_mp3 + orphan:
        try:
            os.remove(f)
            deleted += 1
        except Exception as e:
            print(f"  Gagal hapus {os.path.basename(f)}: {e}")

    print(f"\nTotal dihapus: {deleted}")

    remaining = glob.glob(os.path.join(AUDIO_DIR, "*.mp3"))
    print(f"File MP3 tersisa: {len(remaining)}")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    dry_run = "--delete" not in args
    garbage_only = "--garbage" in args

    print(f"Mode: {'DRY-RUN (tidak hapus)' if dry_run else 'HAPUS'}")
    if garbage_only:
        print("Hanya menghapus kategori garbage: .mp3.mp3 + comma")
    else:
        print("Hapus semua kategori")

    if not os.path.exists(AUDIO_DIR):
        print(f"Folder {AUDIO_DIR} tidak ada")
        sys.exit(0)

    all_files = glob.glob(os.path.join(AUDIO_DIR, "*"))
    expected_filenames = _get_expected_filenames()

    print(f"Total file di disk: {len(all_files)}")

    double_ext = []
    comma_in_name = []
    slash_in_name = []
    non_mp3 = []
    orphan = []

    for f in all_files:
        name = os.path.basename(f)
        if name.endswith(".mp3.mp3"):
            double_ext.append(f)
        elif "/" in name or "\\" in name:
            slash_in_name.append(f)
        elif "\uff0c" in name:
            comma_in_name.append(f)
        elif not name.endswith(".mp3"):
            non_mp3.append(f)
        elif name not in expected_filenames:
            orphan.append(f)

    if garbage_only:
        delete_list = double_ext + comma_in_name
    else:
        delete_list = double_ext + comma_in_name + slash_in_name + non_mp3 + orphan

    print(f"\nTotal yang akan dihapus: {len(delete_list)}")
    for f in delete_list:
        print(f"  {os.path.basename(f)}")

    if dry_run:
        print("\n[MODE DRY-RUN] Tidak ada yang dihapus. Jalankan dengan --delete untuk eksekusi.")
        sys.exit(0)

    deleted = 0
    for f in delete_list:
        try:
            os.remove(f)
            deleted += 1
        except Exception as e:
            print(f"  Gagal hapus {os.path.basename(f)}: {e}")

    print(f"\nTotal dihapus: {deleted}")
    remaining = glob.glob(os.path.join(AUDIO_DIR, "*.mp3"))
    print(f"File MP3 tersisa: {len(remaining)}")