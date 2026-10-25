"""Database lokal: SQLite dengan 2 tabel utama.

Tabel:
  - dictionary:      (hanzi TEXT PRIMARY KEY, jyutping TEXT, definisi TEXT)
  - cached_translations: (indo_text TEXT PRIMARY KEY, hanzi TEXT, jyutping TEXT)
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "charvi_o_data.db")


def get_db_connection():
    """Buka koneksi SQLite dan pastikan tabel sudah ada."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS dictionary (
            hanzi    TEXT PRIMARY KEY,
            jyutping TEXT,
            definisi TEXT
        );

        CREATE TABLE IF NOT EXISTS cached_translations (
            indo_text    TEXT PRIMARY KEY,
            hanzi        TEXT,
            jyutping     TEXT
        );
        """
    )
    conn.commit()
    return conn


def get_cached_translation(indo_text: str):
    """Ambil hasil penerjemahan dari cache, atau None kalau nggak ada."""
    conn = get_db_connection()
    cur = conn.execute(
        "SELECT hanzi, jyutping FROM cached_translations WHERE indo_text = ?",
        (indo_text,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"hanzi": row[0], "jyutping": row[1]}
    return None


def save_to_cache(indo_text: str, hanzi: str, jyutping: str = ""):
    """Simpan hasil penerjemahan ke cache (upsert)."""
    conn = get_db_connection()
    conn.execute(
        """
        INSERT OR REPLACE INTO cached_translations (indo_text, hanzi, jyutping)
        VALUES (?, ?, ?)
        """,
        (indo_text, hanzi, jyutping),
    )
    conn.commit()
    conn.close()


def get_dictionary_entry(hanzi: str):
    """Ambil definisi dari kamus lokal berdasarkan Hanzi."""
    conn = get_db_connection()
    cur = conn.execute(
        "SELECT jyutping, definisi FROM dictionary WHERE hanzi = ?",
        (hanzi,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"jyutping": row[0], "definisi": row[1]}
    return None
