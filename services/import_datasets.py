"""Import open-source Cantonese datasets into a local SQLite database.

Creates `charvi_o_data.db` with two tables:
  - dictionary:      hanzi (PK), jyutping, definisi (from CC-Canto & Rime-Cantonese)
  - cached_translations: indo_text (PK), hanzi, jyutping

Only datasets with allowed licenses are imported:
  - CC-Canto:       CC BY-SA 3.0
  - Rime-Cantonese: LDC (Linguistic Data Consortium)

Usage:
    python -m services.import_datasets
"""

import os
import sqlite3
import urllib.request

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "charvi_o_data.db")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "data", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# URLs
CC_CANTO_URL = (
    "https://raw.githubusercontent.com/amadeusine/cc-canto-data/"
    "master/cccanto-webdist.txt"
)
RIME_CANTONESE_URL = (
    "https://raw.githubusercontent.com/rime/rime-cantonese/"
    "main/jyut6ping3.words.dict.yaml"
)


def get_db_connection():
    """Open the SQLite database and ensure schema exists."""
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


# ---------------------------------------------------------------------------
# CC-Canto importer
# ---------------------------------------------------------------------------
def import_cc_canto() -> int:
    """Download and import CC-Canto (CC BY-SA 3.0) dictionary entries.

    Expected line format: Hanzi [ Jyutping ] { definisi }
    """
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        cache_path = os.path.join(DOWNLOAD_DIR, "cccanto-webdist.txt")

        # Skip if already downloaded
        if not os.path.exists(cache_path):
            req = urllib.request.Request(
                CC_CANTO_URL, headers={"User-Agent": "charvi-o-importer/1.0"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(cache_path, "wb") as f:
                f.write(data)
            print(f"✅ Downloaded CC-Canto to {cache_path}")

        conn = get_db_connection()
        count = 0
        with open(cache_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Parse "Hanzi [ Jyutping ] { definisi }"
                # Example: 漢字 [ jyu4 ] { 魚 }
                hanzi = None
                jyutping = None
                definisi = None

                # Try regex-like parsing (no external deps)
                # Format: Hanzi [ Jyutping ] { definisi }
                import re
                m = re.match(r"^(\S+)\s+\[([^\]]+)\]\s+\{(.+)\}$", line)
                if m:
                    hanzi = m.group(1)
                    jyutping = m.group(2)
                    definisi = m.group(3).strip()

                if hanzi and jyutping and definisi:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO dictionary
                            (hanzi, jyutping, definisi)
                        VALUES (?, ?, ?)
                        """,
                        (hanzi, jyutping, definisi),
                    )
                    count += 1

        conn.commit()
        conn.close()
        print(f"📦 Imported {count} CC-Canto entries.")
        return count
    except Exception as e:
        print(f"❌ Gagal import CC-Canto: {e}")
        return 0


# ---------------------------------------------------------------------------
# Rime-Cantonese importer
# ---------------------------------------------------------------------------
def import_rime_cantonese() -> int:
    """Download and import Rime-Cantonese dictionary entries (LDC)."""
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        cache_path = os.path.join(DOWNLOAD_DIR, "jyut6ping3.words.dict.yaml")

        if not os.path.exists(cache_path):
            req = urllib.request.Request(
                RIME_CANTONESE_URL, headers={"User-Agent": "charvi-o-importer/1.0"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(cache_path, "wb") as f:
                f.write(data)
            print(f"✅ Downloaded Rime-Cantonese to {cache_path}")

        conn = get_db_connection()
        count = 0

        # Rime-Cantonese YAML format: YAML list of entries
        # Each entry has fields like: hanzi, jyutping, cit, ...
        # We parse the raw text for concise Hanzi + Jyutping lines.
        with open(cache_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Skip YAML structure lines (e.g., "entries:", "-", "..." 
                import re
                if re.match(r"^[\-]|^\s*$|^\.", line):
                    continue

                # Look for lines with Hanzi + [ Jyutping ] pattern
                m = re.match(r"^(\S+)\s+\[([^\]]+)\]", line)
                if m:
                    hanzi = m.group(1)
                    jyutping = m.group(2)

                    # Extract definition from { ... } if present
                    dm = re.search(r"\{([^}]+)\}", line)
                    definisi = dm.group(1).strip() if dm else ""

                    if hanzi and jyutping:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO dictionary
                                (hanzi, jyutping, definisi)
                            VALUES (?, ?, ?)
                            """,
                            (hanzi, jyutping, definisi),
                        )
                        count += 1

        conn.commit()
        conn.close()
        print(f"📦 Imported {count} Rime-Cantonese entries.")
        return count
    except Exception as e:
        print(f"❌ Gagal import Rime-Cantonese: {e}")
        return 0


# ---------------------------------------------------------------------------
# Common Voice audio indexer
# ---------------------------------------------------------------------------
def index_audio_common_voice(audio_dir: str = None) -> int:
    """Index Common Voice audio metadata (user-downloaded TSV files).

    This function does NOT download audio (5.99 GB). It only reads the
    metadata TSV files that the user already downloaded manually.

    Expected directory structure (Common Voice):
        common_voice/
            mm/                        # Myanmar (example)
                common_voice_sample.tsv
            en/                        # English (example)
                common_voice_sample.tsv
            ...

    Each TSV has columns: path	sentence	up_votes	down_votes	...
    """
    if audio_dir is None:
        audio_dir = os.path.join(BASE_DIR, "data", "common_voice")

    if not os.path.isdir(audio_dir):
        print(f"⚠️  Common Voice directory not found: {audio_dir}")
        print("   Download manually and re-run.")
        return 0

    conn = get_db_connection()
    count = 0
    tsv_files = []

    # Collect all .tsv files recursively
    for root, _dirs, files in os.walk(audio_dir):
        for fname in files:
            if fname.endswith(".tsv"):
                tsv_files.append(os.path.join(root, fname))

    print(f"📂 Found {len(tsv_files)} metadata TSV files.")

    for tsv_path in tsv_files:
        try:
            with open(tsv_path, "r", encoding="utf-8", errors="replace") as f:
                header = f.readline().strip().split("\t")
                path_idx = header.index("path") if "path" in header else None
                sentence_idx = header.index("sentence") if "sentence" in header else None

                if path_idx is None or sentence_idx is None:
                    continue

                for line in f:
                    parts = line.rstrip("\n").split("\t")
                    if len(parts) <= max(path_idx, sentence_idx):
                        continue
                    file_path = parts[path_idx]
                    transkripsi = parts[sentence_idx]

                    # Only index if transkripsi is non-empty
                    if transkripsi:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO audio_corpus
                                (file_path, transkripsi, sumber)
                            VALUES (?, ?, ?)
                            """,
                            (file_path, transkripsi, "Common Voice (CC BY-SA 4.0)"),
                        )
                        count += 1
        except Exception as e:
            print(f"  ⚠️  Gagal baca {tsv_path}: {e}")
            continue

    conn.commit()
    conn.close()
    print(f"📦 Indexed {count} Common Voice audio entries.")
    return count


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Charvi O — Kantonis Data Importer (Offline-First)")
    print("=" * 60)

    print("\n[1/3] Importing CC-Canto (CC BY-SA 3.0)...")
    import_cc_canto()

    print("\n[2/3] Importing Rime-Cantonese (LDC)...")
    import_rime_cantonese()

    print("\n[3/3] Indexing Common Voice audio metadata (no download)...")
    index_audio_common_voice()

    print("\n✅ Import selesai.")
