import os, glob, re, sqlite3

audio_dir = 'assets/audio_core'
files = glob.glob(os.path.join(audio_dir, '*.mp3'))

# Garbage files
double_ext = set(f for f in files if f.endswith('.mp3.mp3'))
comma_in_name = set(f for f in files if '\uff0c' in os.path.basename(f))
slash = set(f for f in files if '/' in os.path.basename(f) or '\\' in os.path.basename(f))

garbage = double_ext | comma_in_name | slash
print(f'Double-ext files: {len(double_ext)}')
print(f'Comma files: {len(comma_in_name)}')
print(f'Slash files: {len(slash)}')
print(f'Total garbage (union): {len(garbage)}')

# Valid files (not garbage)
valid_files = [f for f in files if f not in garbage]
print(f'\nValid files (not garbage): {len(valid_files)}')

# Expected filenames
db_path = 'charvi_o_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT hanzi FROM cached_translations')
cached_hanzi = [row[0] for row in cursor.fetchall()]
conn.close()

def _safe_audio_filename(hanzi: str) -> str:
    import re
    safe = hanzi
    safe = re.sub(r'[。，、；：！？「」『」（）]', '_', safe)
    safe = re.sub(r'/', '_', safe)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe.strip('_')
    return safe + '.mp3'

expected_filenames = set()
for hanzi in cached_hanzi:
    expected_filenames.add(_safe_audio_filename(hanzi))

print(f'Expected filenames: {len(expected_filenames)}')

# Valid orphan files (valid files whose name is not in expected set)
valid_orphans = []
for f in valid_files:
    basename = os.path.basename(f)
    if basename not in expected_filenames:
        valid_orphans.append(basename)

print(f'Valid orphan files: {len(valid_orphans)}')

# Check if valid orphans differ from expected by only trailing punctuation
punctuation = '？。，、'
matching_after_strip = []
no_match = []
for fname in valid_orphans:
    base = fname[:-4]
    stripped = base.rstrip(punctuation)
    if stripped + '.mp3' in expected_filenames:
        matching_after_strip.append(fname)
    else:
        no_match.append(fname)

print(f'Match after stripping trailing punct: {len(matching_after_strip)}')
print(f'Do NOT match even after stripping: {len(no_match)}')

print('\n--- Sample of "Do NOT match" (valid orphans that cannot be fixed by renaming) ---')
for f in no_match[:15]:
    print(f'  {f}')

print('\n--- Sample of "Match after stripping" (valid orphans that can be renamed) ---')
for f in matching_after_strip[:15]:
    print(f'  {f}')

# Also check: files that are in expected but exist only as garbage
expected_basenames = {os.path.basename(e) for e in expected_filenames}
missing_from_disk = expected_basenames - {os.path.basename(f) for f in valid_files} - {os.path.basename(f) for f in garbage}
print(f'\nExpected files missing entirely from disk: {len(missing_from_disk)}')
