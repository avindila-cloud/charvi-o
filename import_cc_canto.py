"""Import CC-Canto: HANYA Hanzi + Jyutping (tanpa English).

Format file:
  一件還一件 [yi1 jian4 hai2 yi2 jian4] {jat1 gin6 waan4 jat1 gin6}
       ↑              ↑                          ↑
    hanzi          pinyin                      jyutping
                  (skip)                        (ambil)
"""
import urllib.request
import sqlite3
import re


URL = "https://raw.githubusercontent.com/amadeusine/cc-canto-data/master/cccanto-webdist.txt"
DB_PATH = "charvi_o_data.db"


def import_cc_canto():
    print(f"Downloading CC-Canto...")
    try:
        with urllib.request.urlopen(URL, timeout=120) as r:
            content = r.read().decode("utf-8", errors="ignore")
        print(f"Downloaded: {len(content):,} bytes")
    except Exception as e:
        print(f"DOWNLOAD GAGAL: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Pastikan tabel ada (schema existing, jangan diubah)
    c.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hanzi TEXT NOT NULL,
            jyutping TEXT,
            definisi TEXT,
            sumber TEXT DEFAULT 'CC-Canto'
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_dict_hanzi ON dictionary(hanzi)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_dict_jyut ON dictionary(jyutping)")

    # Hapus data lama CC-Canto (re-import bersih)
    old_count = c.execute("SELECT COUNT(*) FROM dictionary WHERE sumber='CC-Canto'").fetchone()[0]
    c.execute("DELETE FROM dictionary WHERE sumber='CC-Canto'")
    print(f"Hapus {old_count:,} row lama CC-Canto")

    lines = content.strip().split("\n")
    print(f"Parsing {len(lines):,} baris...")

    batch = []
    skipped = 0
    inserted = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Format: hanzi [pinyin] {jyutping}
        # Group 1 = hanzi, Group 2 = pinyin (skip), Group 3 = jyutping
        m = re.match(r"^([^\[]+?)\s*\[([^\]]+)\]\s*\{([^}]+)\}", line)
        if not m:
            skipped += 1
            continue

        hanzi = m.group(1).strip()
        jyutping = m.group(3).strip()  # ← AMBIL dari kurung kurawal

        if not hanzi or not jyutping:
            skipped += 1
            continue

        batch.append((hanzi, jyutping))
        inserted += 1

        if len(batch) >= 1000:
            c.executemany(
                "INSERT INTO dictionary (hanzi, jyutping, definisi, sumber) "
                "VALUES (?, ?, NULL, 'CC-Canto')",
                batch
            )
            batch = []
            print(f"  Progress: {inserted:,} inserted...")

    if batch:
        c.executemany(
            "INSERT INTO dictionary (hanzi, jyutping, definisi, sumber) "
            "VALUES (?, ?, NULL, 'CC-Canto')",
            batch
        )

    conn.commit()

    total = c.execute("SELECT COUNT(*) FROM dictionary WHERE sumber='CC-Canto'").fetchone()[0]

    # Verifikasi sample
    print("=== SAMPLE 5 ROWS ===")
    c.execute("SELECT hanzi, jyutping, definisi FROM dictionary WHERE sumber='CC-Canto' LIMIT 5")
    for row in c.fetchall():
        print(f"  hanzi={row[0]!r}  jyutping={row[1]!r}  definisi={row[2]!r}")

    # Cek 早晨
    print("\n=== CEK 早晨 ===")
    c.execute("SELECT hanzi, jyutping FROM dictionary WHERE hanzi='早晨'")
    rows = c.fetchall()
    for row in rows:
        print(f"  {row[0]} -> {row[1]}")
    if not rows:
        print("  ⚠️ 早晨 tidak ditemukan!")

    # Cek satu entry yang tadi salah
    print("\n=== CEK 一件還一件 ===")
    c.execute("SELECT hanzi, jyutping FROM dictionary WHERE hanzi='一件還一件'")
    rows = c.fetchall()
    for row in rows:
        print(f"  {row[0]} -> {row[1]}")

    conn.close()

    print(f"\n✅ IMPORT SELESAI")
    print(f"   Total CC-Canto: {total:,}")
    print(f"   Skipped: {skipped:,}")


if __name__ == "__main__":
    import_cc_canto()
