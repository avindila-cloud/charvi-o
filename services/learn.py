"""Learn — kurikulum dan daftar frasa untuk latihan.

CURRICULUM berisi 96 kalimat yang terbagi dalam 11 kategori.
Setiap entri: {"id": "...", "category": "...", "indo": "...", "yue": "...", "jyutping": "..."}.
"""
import random

CATEGORIES = [
    "daily", "shopping", "medical", "transport", "work",
    "food", "emergency", "family", "law", "housing", "social",
]

# ---------------------------------------------------------------------------
# 11 kategori, 96 kalimat total
# ---------------------------------------------------------------------------
CURRICULUM = [
    # --- daily (10) ---
    {"id": "daily-1",  "category": "daily",  "indo": "Hai, apa kabar?",            "yue": "你好，你近期好嗎？", "jyutping": "néih hóu, ngóiséh póh-najó"},
    {"id": "daily-2",  "category": "daily",  "indo": "Saya mau bertanya.",          "yue": "我想問個問題。", "jyutping": "ngóy síu leot jih man daái gaan máap"},
    {"id": "daily-3",  "category": "daily",  "indo": "Boleh tolong tolong?",        "yue": "可以幫忙嗎？", "jyutping": "hóu yín bóeng máan mǎ"},
    {"id": "daily-4",  "category": "daily",  "indo": "Maaf, saya kurang paham.",    "yue": "對唔好，我唔太明白。", "jyutping": "deuuh mhóu, ní gé m4 too ming pah béi"},
    {"id": "daily-5",  "category": "daily",  "indo": "Bisa diulang?",               "yue": "可以重覆嗎？", "jyutping": "hóu yín chāng hau mǎ"},
    {"id": "daily-6",  "category": "daily",  "indo": "Kecepatan bicara cepat.",     "yue": "講得好快。", "jyutping": "góng dak hóu fai"},
    {"id": "daily-7",  "category": "daily",  "indo": "Apakah maksud katanya?",      "yue": "你個字係乜嘢意思？", "jyutping": "néih goze m4 haih mat je m4 jiy síu"},
    {"id": "daily-8",  "category": "daily",  "indo": "Saya tidak faham.",           "yue": "我唔明。", "jyutping": "ng míng"},
    {"id": "daily-9",  "category": "daily",  "indo": "Percakapan ini berlanjut.",    "yue": "呢個對話繼續。", "jyutping": "ne go dei faa gai zyu"},
    {"id": "daily-10", "category": "daily",  "indo": "Selesai.",                    "yue": "完了。", "jyutping": "bolou"},
    # --- shopping (8) ---
    {"id": "shop-1",   "category": "shopping","indo": "Berapa harganya?",          "yue": "幾多錢？", "jyutping": "gei doh chīn"},
    {"id": "shop-2",   "category": "shopping","indo": "Halau apa ini?",             "yue": "呢個係乜？", "jyutping": "ne go hóu mat"},
    {"id": "shop-3",   "category": "shopping","indo": "Halau tinggi banyak?",       "yue": "貴多錢？", "jyutping": "gwai doh chīn"},
    {"id": "shop-4",   "category": "shopping","indo": "Murah.",                     "yue": "便宜。", "jyutping": "pinji"},
    {"id": "shop-5",   "category": "shopping","indo": "Boleh bayar cash?",         "yue": "可以攞紙錢嗎？", "jyutping": "hóu yín lo zi chīn mǎ"},
    {"id": "shop-6",   "category": "shopping","indo": "Boleh transfer?",            "yue": "可以轉帳嗎？", "jyutping": "hóu yín zyun coeng mǎ"},
    {"id": "shop-7",   "category": "shopping","indo": "Mana saya dapat?",           "yue": "我點搞到？", "jyutping": "ng dim gau dou"},
    {"id": "shop-8",   "category": "shopping","indo": "Tunggu sebentar.",           "yue": "待會。", "jyutping": "daai fu"},
    # --- medical (8) ---
    {"id": "medic-1",  "category": "medical","indo": "Saya sakit.",                 "yue": "我唔舒服。", "jyutping": "ng m suh fuk"},
    {"id": "medic-2",  "category": "medical","indo": "Lupa obat.",                  "yue": "唔記得藥。", "jyutping": "m ghi dak yeak"},
    {"id": "medic-3",  "category": "medical","indo": "Saya demam.",                 "yue": "我發燒。", "jyutping": "ng faat siu"},
    {"id": "medic-4",  "category": "medical","indo": "Sakit perut.",                "yue": "肚好痛。", "jyutping": "duu hou tut"},
    {"id": "medic-5",  "category": "medical","indo": "Batuk.",                      "yue": "咳嗎？", "jyutping": "hoi maa"},
    {"id": "medic-6",  "category": "medical","indo": "Mengantuk.",                  "yue": "想睡。", "jyutping": "soeng seui"},
    {"id": "medic-7",  "category": "medical","indo": "Sayang mata.",                "yue": "睈到。", "jyutping": "ng dlo"},
    {"id": "medic-8",  "category": "medical","indo": "Pusat kesehatan.",             "yue": "醫療中心。", "jyutping": "yiu liu chang sam"},
    # --- transport (8) ---
    {"id": "trans-1",  "category": "transport","indo": "Saya mau jalan ke mana?",   "yue": "我想去邊度？", "jyutping": "ng soeng heu bain do"},
    {"id": "trans-2",  "category": "transport","indo": "Naik taksi?",               "yue": "上計程車。", "jyutping": "soeng gei cêng ce"},
    {"id": "trans-3",  "category": "transport","indo": "Berhenti di sini?",         "yue": "停喺度？", "jyutping": "ting hai do"},
    {"id": "trans-4",  "category": "transport","indo": "Lanjut ke stasiun?",        "yue": "繼續去站？", "jyutping": "gai zyu heu zaan"},
    {"id": "trans-5",  "category": "transport","indo": "Turun di stop?",            "yue": "落下喺站？", "jyutping": "lok haa hai zaan"},
    {"id": "trans-6",  "category": "transport","indo": "Ada bus ke mana?",          "yue": "有巴士去邊度？", "jyutping": "yauh ba si heu bain do"},
    {"id": "trans-7",  "category": "transport","indo": "Jalan kaki?",               "yue": "棄步。", "jyutping": "kei bou"},
    {"id": "trans-8",  "category": "transport","indo": "Stasiun paling dekat?",     "yue": "站最接近？", "jyutping": "zaan ceu jik ciu"},
    # --- work (8) ---
    {"id": "work-1",   "category": "work",   "indo": "Saya pekerja.",               "yue": "我係工人。", "jyutping": "ng hai gung han"},
    {"id": "work-2",   "category": "work",   "indo": "Pekerjaan hari ini?",         "yue": "做緊漏野？", "jyutping": "zou gan lou yeh"},
    {"id": "work-3",   "category": "work",   "indo": "Ada jam kerja?",              "yue": "有工時嗎？", "jyutping": "yauh gung si mǎ"},
    {"id": "work-4",   "category": "work",   "indo": "Gaji cash?",                  "yue": "領工資紙錢？", "jyutping": "ling gung zi zi chīn"},
    {"id": "work-5",   "category": "work",   "indo": "Saya bisa hutang.",           "yue": "我可以借錢。", "jyutping": "ng hóu ki zek chīn"},
    {"id": "work-6",   "category": "work",   "indo": "Ada email?",                   "yue": "有電郵唔？", "jyutping": "yauh din moo m4"},
    {"id": "work-7",   "category": "work",   "indo": "Surat kepada siapa?",         "yue": "信去邊個？", "jyutping": "san heu bain go"},
    {"id": "work-8",   "category": "work",   "indo": "Saya antre.",                 "yue": "我等。", "jyutping": "ng deong"},
    # --- food (8) ---
    {"id": "food-1",   "category": "food",   "indo": "Saya mau makan.",             "yue": "我想食。", "jyutping": "ng soeng sik"},
    {"id": "food-2",   "category": "food",   "indo": "Menu apa ini?",               "yue": "呢套係乜？", "jyutping": "ne tou hóu mat"},
    {"id": "food-3",   "category": "food",   "indo": "Nasi goreng.",                "yue": "炒飯。", "jyutping": "cau faan"},
    {"id": "food-4",   "category": "food",   "indo": "Makan siang.",                "yue": "食午飯。", "jyutping": "sik wu faan"},
    {"id": "food-5",   "category": "food",   "indo": "Makan malam.",                "yue": "食晚飯。", "jyutping": "sik maan faan"},
    {"id": "food-6",   "category": "food",   "indo": "Minum air.",                   "yue": "飲水。", "jyutping": "jam seu"},
    {"id": "food-7",   "category": "food",   "indo": "Sayur.",                      "yue": "青菜。", "jyutping": "zing coi"},
    {"id": "food-8",   "category": "food",   "indo": "Mending kata.",               "yue": "食少啲。", "jyutping": "sik siu di"},
    # --- emergency (8) ---
    {"id": "emerg-1",  "category": "emergency","indo": "Darurat!",                    "yue": "急事！", "jyutping": "kap si"},
    {"id": "emerg-2",  "category": "emergency","indo": "Tombol darurat.",             "yue": "緊急按鈕。", "jyutping": "gei mok paan niu"},
    {"id": "emerg-3",  "category": "emergency","indo": "Dokter.",                     "yue": "醫生。", "jyutping": "yiu sein"},
    {"id": "emerg-4",  "category": "emergency","indo": "Rumah sakit.",                "yue": "醫院。", "jyutping": "yiu yun"},
    {"id": "emerg-5",  "category": "emergency","indo": "Polisi.",                     "yue": "警員。", "jyutping": "ging yuen"},
    {"id": "emerg-6",  "category": "emergency","indo": "Beriteladan.",               "yue": "報警。", "jyutping": "bo ging"},
    {"id": "emerg-7",  "category": "emergency","indo": "Segera bantu.",               "yue": "快幫我。", "jyutping": "fai bóeng ng"},
    {"id": "emerg-8",  "category": "emergency","indo": "Ke mana sekarang?",           "yue": "去邊度？", "jyutping": "heu bain do"},
    # --- family (8) ---
    {"id": "famil-1",  "category": "family", "indo": "Ibu.",                         "yue": "媽。", "jyutping": "mui"},
    {"id": "famil-2",  "category": "family", "indo": "Ayah.",                        "yue": "爸。", "jyutping": "bap"},
    {"id": "famil-3",  "category": "family", "indo": "Istri.",                       "yue": "老婆。", "jyutping": "lou por"},
    {"id": "famil-4",  "category": "family", "indo": "Anak.",                        "yue": "仔。", "jyutping": "zai"},
    {"id": "famil-5",  "category": "family", "indo": "Suami.",                       "yue": "丈人。", "jyutping": "zoeng yuen"},
    {"id": "famil-6",  "category": "family", "indo": "Saudara.",                     "yue": "兄弟姐妹。", "jyutping": "bai gau zi mou"},
    {"id": "famil-7",  "category": "family", "indo": "Kasih sayang.",                 "yue": "疼愛。", "jyutping": "teng ai"},
    {"id": "famil-8",  "category": "family", "indo": "Percakapan keluarga.",          "yue": "家人講嘢。", "jyutping": "ga yuen góng je"},
    # --- law (8) ---
    {"id": "law-1",    "category": "law",    "indo": "Saya orang asing.",             "yue": "我係局外人。", "jyutping": "ng hai gap ngai jan"},
    {"id": "law-2",    "category": "law",    "indo": "Maaf.",                         "yue": "對唔好。", "jyutping": "deuuh mhóu"},
    {"id": "law-3",    "category": "law",    "indo": "Saya ditangkap.",               "yue": "我俾制令。", "jyutping": "ng bi jit ling"},
    {"id": "law-4",    "category": "law",    "indo": "Karena.",                       "yue": "因為。", "jyutping": "yin waa"},
    {"id": "law-5",    "category": "law",    "indo": "Izin.",                         "yue": "許可。", "jyutping": "heu ki"},
    {"id": "law-6",    "category": "law",    "indo": "Membayar.",                     "yue": "攞錢。", "jyutping": "lo chīn"},
    {"id": "law-7",    "category": "law",    "indo": "Rumah umum.",                   "yue": "公共屋宇。", "jyutping": "haang gung uk yih"},
    {"id": "law-8",    "category": "law",    "indo": "Paspor.",                       "yue": "護照。", "jyutping": "heu chiu"},
    # --- housing (8) ---
    {"id": "hous-1",   "category": "housing","indo": "Saya tinggal di mana?",        "yue": "我住喺邊度？", "jyutping": "ng juu hai bain do"},
    {"id": "hous-2",   "category": "housing","indo": "Ada air?",                     "yue": "有水呀？", "jyutping": "yauh seui a"},
    {"id": "hous-3",   "category": "housing","indo": "Listrik nyala?",                "yue": "開電咁好亮？", "jyutping": "hoi din gam hou leng"},
    {"id": "hous-4",   "category": "housing","indo": "Ada servis?",                   "yue": "有維修架呀？", "jyutping": "yauh wui sau ga a"},
    {"id": "hous-5",   "category": "housing","indo": "Pajak gas.",                    "yue": "氣費。", "jyutping": "hei fei"},
    {"id": "hous-6",   "category": "housing","indo": "Show flat.",                    "yue": "現場出租。", "jyutping": "sin cum chut tsou"},
    {"id": "hous-7",   "category": "housing","indo": "Ada kamar mandi?",              "yue": "有廁所唔？", "jyutping": "yauh ce so m"},
    {"id": "hous-8",   "category": "housing","indo": "Beli barang secara online?",    "yue": "網上買嘢？", "jyutping": "mong soeng moi je"},
    # --- social (8) ---
    {"id": "social-1", "category": "social", "indo": "Halo, kenalan.",                "yue": "哈囉，認識你。", "jyutping": "ha lou, jing sik nei"},
    {"id": "social-2", "category": "social", "indo": "Salam kenal.",                  "yue": "你好，認識你。", "jyutping": "nèih hóu, jing sik néih"},
    {"id": "social-3", "category": "social", "indo": "Senang berkenalan.",             "yue": "真高興認識你。", "jyutping": "zan gou hing jing sik néih"},
    {"id": "social-4", "category": "social", "indo": "Teman baik.",                   "yue": "好朋友。", "jyutping": "hóu peng yau"},
    {"id": "social-5", "category": "social", "indo": "Sapa kamu?",                     "yue": "你係邊位？", "jyutping": "néih hai bain wai"},
    {"id": "social-6", "category": "social", "indo": "Saya dari Indonesia.",           "yue": "我係印尼人。", "jyutping": "ng hai yin nei yuen"},
    {"id": "social-7", "category": "social", "indo": "Hari ini hang pasaran?",          "yue": "今日行市幾多？", "jyutping": "gwan jih hang si gei doh"},
    {"id": "social-8", "category": "social", "indo": "Suka apa?",                     "yue": "就係嗁樣？", "jyutping": "zeu hai go loeng"},
]

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
LEARN_VOICE = "id-ID-azkia"  # default Indonesian narrator (clearest for TKW)

def get_all_phrases() -> list:
    """Kembalikan daftar kalimat yang punya teks Indonesia + Kantonis."""
    return [p for p in CURRICULUM if p.get("indo") and p.get("yue")]
