"""Import Daily Cantonese Dataset (leeduckgo/cantonese-life-scenarios-corpus).

Steps:
1. Read index.csv (UTF-8, 5 columns: 序号, 粤语原文, 普通话翻译, 香港语言学会粤拼, 场景)
2. Create canto_daily table in charvi_o_data.db
3. Import data with audio paths
"""
import csv
import sqlite3
import os
import re
import sys
import zipfile

# Paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(ROOT_DIR, "temp_canto_download", "index.csv")
DATA_ZIP_PATH = os.path.join(ROOT_DIR, "temp_canto_download", "data.zip")
AUDIO_DIR = os.path.join(ROOT_DIR, "assets", "audio_canto_daily")
DB_PATH = os.path.join(ROOT_DIR, "charvi_o_data.db")
BATCH_SIZE = 500


def parse_scenario(scenario_str):
    """Parse scenario column to extract scenario name."""
    match = re.match(r"^(\d+)(.*)", scenario_str.strip())
    if match:
        return match.group(2).strip()
    return scenario_str.strip()


def import_daily_canto():
    """Main import function."""
    print("=" * 60)
    print("IMPORT DAILY CANTONESE DATASET")
    print("=" * 60)
    
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV file not found: {CSV_PATH}")
        return
    
    os.makedirs(AUDIO_DIR, exist_ok=True)
    print(f"Audio directory: {AUDIO_DIR}")
    
    # Read CSV
    print(f"\nReading CSV: {CSV_PATH}")
    rows = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"Total rows: {len(rows)}")
    
    for row in rows:
        row['scenario_clean'] = parse_scenario(row['场景'])
    
    scenario_counts = {}
    for row in rows:
        scenario = row['scenario_clean']
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
    
    print(f"\nScenarios: {len(scenario_counts)}")
    for scenario, count in sorted(scenario_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {scenario}: {count}")
    
    # Create database connection
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\nCreating canto_daily table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS canto_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            yue_text TEXT NOT NULL,
            mandarin_text TEXT,
            jyutping TEXT,
            scenario TEXT,
            audio_path TEXT,
            indo_text TEXT,
            sumber TEXT DEFAULT 'leeduckgo'
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_daily_yue ON canto_daily(yue_text)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_daily_jyut ON canto_daily(jyutping)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_daily_indo ON canto_daily(indo_text)")
    
    # Delete existing data
    c.execute("DELETE FROM canto_daily")
    print("Cleared existing canto_daily data")
    
    # Prepare data
    print("\nImporting data (TTS on-demand)...")
    batch = []
    imported = 0

    for row in rows:
        yue_text = row['粤语原文'].strip()
        mandarin_text = row['普通话翻译'].strip() if row['普通话翻译'] else None
        jyutping = row['香港语言学会粤拼'].strip() if row['香港语言学会粤拼'] else None
        scenario = row['scenario_clean']
        sumber = 'leeduckgo'
        indo_text = None
        audio_path = None  # TTS on-demand, tidak pakai audio lokal

        batch.append((
            yue_text,
            mandarin_text,
            jyutping,
            scenario,
            audio_path,
            indo_text,
            sumber
        ))

        if len(batch) >= BATCH_SIZE:
            c.executemany(
                """INSERT INTO canto_daily 
                (yue_text, mandarin_text, jyutping, scenario, audio_path, indo_text, sumber)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                batch
            )
            imported += len(batch)
            batch = []
            if imported % 1000 == 0:
                print(f"  Imported {imported:,} rows...")
    
    if batch:
        c.executemany(
            """INSERT INTO canto_daily 
            (yue_text, mandarin_text, jyutping, scenario, audio_path, indo_text, sumber)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            batch
        )
        imported += len(batch)
    
    conn.commit()
    print(f"\n✅ Imported {imported:,} rows into canto_daily")
    
    # Verify
    c.execute("SELECT COUNT(*) FROM canto_daily")
    total = c.fetchone()[0]
    print(f"Total rows in canto_daily: {total}")
    
    c.execute("SELECT * FROM canto_daily LIMIT 3")
    print("\nSample rows:")
    for row in c.fetchall():
        print(f"  yue_text: {row[1]}")
        print(f"  mandarin_text: {row[2]}")
        print(f"  jyutping: {row[3]}")
        print(f"  scenario: {row[4]}")
        print(f"  audio_path: {row[5]}")
        print(f"  indo_text: {row[6]}")
        print(f"  sumber: {row[7]}")
        print()
    
    conn.close()
    print("=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import_daily_canto()
