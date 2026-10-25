"""LLM — penerjemahan teks lewat Groq API (Llama 3.3 70B).

Contoh penggunaan:
    from services.translate import translate
    terjemahan = translate("Saya mau pergi", "id", "yue")
"""
import os
from dotenv import load_dotenv
load_dotenv()

SYSTEM_PROMPT = """Anda adalah penutur asli (native speaker) Bahasa Kantonis dari Hong Kong. Tugas Anda menerjemahkan teks dari Bahasa Indonesia ke Bahasa Kantonis (atau sebaliknya).

ATURAN MUTLAK:
1. DILARANG MENERJEMAHKAN KATA PER KATA. Terjemahkan berdasarkan makna utuh kalimat.
2. GUNAKAN BAHASA LISAN (口語) SEHARI-HARI, bukan bahasa tulis/baku (書面語). Ini untuk percakapan dengan majikan, TKW, atau di pasar.
3. WAJIB GUNAKAN PARTIKEL KHAS KANTONIS (seperti: 呀, 喇, 咗, 緊, 嘅, 唔, 冇, 睇, 食).
4. DILARANG MENGGUNAKAN TATA BAHASA MANDARIN (seperti: 的, 是, 了, 不, 没).
5. Gunakan karakter Hanzi Tradisional (香港字).
6. Jika hasilnya terasa kaku, ubah menjadi bentuk percakapan yang paling wajar diucapkan orang Hong Kong.

CONTOH BENAR:
- ID: "Saya sudah makan." -> HK: "我食咗飯喇。" (BUKAN: 我已经吃饭了)
- ID: "Mau pergi ke mana?" -> HK: "去边度呀？" (BUKAN: 去哪里)
- ID: "Tolong bantu saya." -> HK: "唔该帮嗮我。" (BUKAN: 请帮助我)
- ID: "Saya tidak mengerti." -> HK: "我唔明白呀。" (BUKAN: 我不明白)

Hanya keluarkan hasil terjemahannya saja (Hanzi), tanpa penjelasan tambahan atau romanisasi Latin.
"""

from groq import Groq


def translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """Terjemahkan teks satu baris dari src_lang ke tgt_lang.

    Args:
        text:      Teks sumber (Indonesia atau Kantonis).
        src_lang:  "id" (Indonesia) atau "yue" (Kantonis).
        tgt_lang:  "yue" (Kantonis) atau "id" (Indonesia).

    Returns:
        Teks yang sudah diterjemahkan, bersih spasi/newline.
    """
    if not text or not text.strip():
        return ""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Dari {src_lang} ke {tgt_lang}: {text}"}
        ],
        temperature=0.3,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()
