"""Clear audio_path di canto_daily (skip audio download, pakai TTS)."""

import sqlite3


DB_PATH = "charvi_o_data.db"


def cleanup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Clear audio_path (karena file tidak ada / gagal download)
    c.execute("UPDATE canto_daily SET audio_path = NULL")
    conn.commit()
    print(f"Audio_path di-clear untuk semua row")

    # Verifikasi
    c.execute("SELECT COUNT(*) FROM canto_daily")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM canto_daily WHERE audio_path IS NULL")
    null_count = c.fetchone()[0]

    print(f"Total canto_daily: {total:,}")
    print(f"Audio_path NULL: {null_count:,}")
    print(f"Semua audio akan di-generate via TTS saat user play")

    # Sample 5
    print("\n=== SAMPLE 5 ===")
    c.execute("SELECT yue_text, jyutping, scenario FROM canto_daily LIMIT 5")
    for row in c.fetchall():
        print(f"  {row[0]} | {row[1]} | {row[2]}")

    # Distribusi scenario
    print("\n=== TOP 10 SKENARIO ===")
    c.execute("""
        SELECT scenario, COUNT(*) FROM canto_daily
        GROUP BY scenario ORDER BY COUNT(*) DESC LIMIT 10
    """)
    for sc, cnt in c.fetchall():
        print(f"  {sc}: {cnt:,}")

    conn.close()


if __name__ == "__main__":
    cleanup()
