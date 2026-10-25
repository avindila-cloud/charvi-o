
import os, glob, sqlite3, re
from services.seed_queue import _safe_audio_filename

AUDIO_DIR = 'assets/audio_core'
all_files = glob.glob(os.path.join(AUDIO_DIR, '*'))
expected = set()
conn = sqlite3.connect('charvi_o_data.db')
c = conn.cursor()
c.execute('SELECT hanzi FROM cached_translations')
hanzi_list = [row[0] for row in c.fetchall() if row[0]]
conn.close()
for hanzi in hanzi_list:
    expected.add(_safe_audio_filename(hanzi))

# Categorize
double_ext = [f for f in all_files if os.path.basename(f).endswith('.mp3.mp3')]
comma_in_name = [f for f in all_files if chr(0xFF0C) in os.path.basename(f)]
slash_in_name = [f for f in all_files if '/' in os.path.basename(f) or chr(92) in os.path.basename(f)]
non_mp3 = [f for f in all_files if not os.path.basename(f).endswith('.mp3')]

# Orphan: .mp3, no double ext, no comma, no slash, no non-mp3, name not in expected
orphan = []
for f in all_files:
    name = os.path.basename(f)
    if name.endswith('.mp3') and not name.endswith('.mp3.mp3') and chr(0xFF0C) not in name and '/' not in name and chr(92) not in name and name not in expected:
        orphan.append(f)

print(f'Total: {len(all_files)}')
print(f'.mp3.mp3: {len(double_ext)}')
print(f'Comma: {len(comma_in_name)}')
print(f'Slash: {len(slash_in_name)}')
print(f'Non-mp3: {len(non_mp3)}')
print(f'Orphan: {len(orphan)}')

# Check orphan names with trailing punct
strip_punct = re.compile(r'([。，、；：！？])$')  # strip trailing punct before .mp3
matched = []
unmatched = []
for f in orphan:
    name = os.path.basename(f)
    base = strip_punct.sub('', name)  # strip trailing punct
    if base in expected:
        matched.append(f)
    else:
        unmatched.append(f)

print(f'Orphan matching after stripping trailing punct: {len(matched)}')
print(f'Orphan NOT matching even after strip: {len(unmatched)}')

# For unmatched, show examples
for f in unmatched[:10]:
    print(f'  UNMATCHED: {os.path.basename(f)}')
