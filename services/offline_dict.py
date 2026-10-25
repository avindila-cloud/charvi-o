"""Offline dictionary & caching for Cantonese translation.

Queries a local SQLite DB (`cached_cantonese.db`) before calling the
Gemini API, and caches successful translations for instant future lookup.
"""

import os
import sqlite3

# Project root is two levels up from this file (services/ -> charvi-o/).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "assets", "audio", "cached_cantonese.db")


def get_db_connection():
    """Open (and lazily create) the SQLite database connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dictionary (
            indo_text    TEXT PRIMARY KEY,
            kantonis_hanzi TEXT,
            jyutping     TEXT,
            audio_path   TEXT
        )
        """
    )
    conn.commit()
    return conn


def get_cached_translation(text_indo: str) -> dict | None:
    """Return cached translation dict, or None if not found."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT indo_text, kantonis_hanzi, jyutping, audio_path FROM dictionary WHERE indo_text = ?",
            (text_indo.strip(),),
        ).fetchone()
        if row is None:
            return None
        return {
            "indo_text": row[0],
            "kantonis_hanzi": row[1],
            "jyutping": row[2],
            "audio_path": row[3],
        }
    finally:
        conn.close()


def save_to_cache(text_indo: str, hanzi: str, jyutping: str, audio_path: str | None = None) -> None:
    """Insert or update a translation entry in the cache."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO dictionary (indo_text, kantonis_hanzi, jyutping, audio_path)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(indo_text) DO UPDATE SET
                kantonis_hanzi = excluded.kantonis_hanzi,
                jyutping     = excluded.jyutping,
                audio_path   = excluded.audio_path
            """,
            (text_indo.strip(), hanzi.strip(), jyutping.strip(), audio_path),
        )
        conn.commit()
    finally:
        conn.close()
