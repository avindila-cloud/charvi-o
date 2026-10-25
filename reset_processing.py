import sqlite3

conn = sqlite3.connect('charvi_o_data.db')
c = conn.cursor()

# Reset yang nyangkut
c.execute("UPDATE translation_queue SET status='pending' WHERE status='processing'")
conn.commit()
print(f'✅ Reset: {c.rowcount} item kembali ke pending')

# Tampilkan state
print('\n=== State Setelah Reset ===')
c.execute('SELECT status, COUNT(*) FROM translation_queue GROUP BY status')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

c.execute('SELECT COUNT(*) FROM cached_translations')
print(f'\nCached translations: {c.fetchone()[0]}')

conn.close()