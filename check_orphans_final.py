import os, glob, re, sqlite3

audio_dir = 'assets/audio_core'
files = glob.glob(os.path.join(audio_dir, '*.mp3'))

total = len(files)
print(f'Total MP3 files: {total}')

double_ext = [f for f in files if f.endswith('.mp3.mp3')]
print(f'.mp3.mp3: {len(double_ext)}')

comma_in_name = [f for f in files if '\uff0c' in os.path.basename(f)]
print(f'Comma: {len(comma_in_name)}')

slash = [f for f in files if '/' in os.path.basename(f) or '\\' in os.path.basename(f)]
print(f'Slash: {len(slash)}')

non_mp3 = [f for f in files if not f.endswith('.mp3')]
print(f'Non-mp3: {len(non_mp3)}')

# Get expected filenames from SQLite
db_path = 'charvi_o_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT hanzi FROM cached_translations')
cached_hanzi = [row[0] for row in cursor.fetchall()]
conn.close()

print(f'Total cached translations: {len(cached_hanzi)}')

def _safe_audio_filename(hanzi: str) -> str:
    safe = hanzi
    safe = re.sub(r'[。，、；：！？「」『」（）]', '_', safe)
    safe = re.sub(r'/', '_', safe)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe.strip('_')
    return safe + '.mp3'

expected_filenames = set()
for hanzi in cached_hanzi:
    expected_filenames.add(_safe_audio_filename(hanzi))

orphans = []
for f in files:
    basename = os.path.basename(f)
    if basename not in expected_filenames:
        orphans.append(basename)

print(f'Orphans (not in expected): {len(orphans)}')

punctuation = '？。，、'
matches_after_strip = []
no_match = []
for fname in orphans:
    base = fname[:-4]
    stripped = base.rstrip(punctuation)
    if stripped + '.mp3' in expected_filenames:
        matches_after_strip.append(fname)
    else:
        no_match.append(fname)

print(f'Match after stripping trailing punct: {len(matches_after_strip)}')
print(f'Do NOT match even after stripping: {len(no_match)}')
print()
print('Sample of do NOT match:')
for f in no_match[:10]:
    print(f'  {f}')
