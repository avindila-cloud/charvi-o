
import sqlite3
from services.seed_queue import _safe_audio_filename
conn = sqlite3.connect('charvi_o_data.db')
c = conn.cursor()
c.execute("SELECT hanzi FROM cached_translations WHERE hanzi LIKE '%ATM%' OR hanzi LIKE '%有冴%' OR hanzi LIKE '%連線%' OR hanzi LIKE '%幾多%' OR hanzi LIKE '%順風%' OR hanzi LIKE '%喺邊度%' OR hanzi LIKE '%付款%' OR hanzi LIKE '%買嘢%' OR hanzi LIKE '%交藥%' OR hanzi LIKE '%天氣%' OR hanzi LIKE '%冇錢%' OR hanzi LIKE '%開戶%' OR hanzi LIKE '%重置%' OR hanzi LIKE '%領工資%' OR hanzi LIKE '%轉帳%' OR hanzi LIKE '%網絡%' OR hanzi LIKE '%晾衫%' OR hanzi LIKE '%繼續%' OR hanzi LIKE '%食午%' OR hanzi LIKE '%食飯%' OR hanzi LIKE '%食糊%' OR hanzi LIKE '%食夜飯%' OR hanzi LIKE '%吃藥%' OR hanzi LIKE '%打車%' OR hanzi LIKE '%坐車%' OR hanzi LIKE '%點樣%' GROUP BY hanzi ORDER BY hanzi")
for row in c.fetchall():
    src = _safe_audio_filename(row[0])
    indent = '  '
    print(f'{indent}CACHE: {row[0]!r}')
    print(f'{indent}SAFE : {src!r}')
conn.close()
