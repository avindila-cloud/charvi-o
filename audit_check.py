
import sqlite3
conn = sqlite3.connect('charvi_o_data.db')
c = conn.cursor()
for kw in ['ATM', '有冴', '連線', '喺邊度', '幾多', '順風', '付款', '買嘢', '藥', '天氣', '冇錢', '開戶', '重置', '領工資', '轉帳', '網絡', '晾衫', '繼續', '食午', '食糊', '食飯', '食夜飯', '吃藥', '打車', '坐車', '點樣']:
    c.execute("SELECT hanzi, COUNT(*) as cnt FROM cached_translations WHERE hanzi LIKE ? GROUP BY hanzi ORDER BY cnt DESC", (f'%{kw}%',))
    rows = c.fetchall()
    if rows:
        print(f"--- {kw} ---")
        for r in rows[:5]:
            print(f"  {r[0]} ({r[1]})")
conn.close()
