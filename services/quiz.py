"""Quiz — soalan pilihan ganda untuk latihan.

Setiap soalan meminta pengguna memilih terjemahan Kantonis yang betul
berdasarkan teks Indonesia.
"""
import random

from .learn import CURRICULUM, get_all_phrases

DEFAULT_TOTAL = 5


def build_quiz(category=None, total: int = DEFAULT_TOTAL) -> list:
    """Bina senarai soalan pilihan ganda.

    Returns:
        Senarai dict soalan:
        [
          {"indo": "...", "jyutping": "...", "options": [...], "answer_index": n},
          ...
        ]
    """
    pool = [p for p in get_all_phrases()
            if (not category or p.get("category") == category)]
    pool = [p for p in pool if p.get("indo") and p.get("yue")]
    if not pool:
        return []
    random.shuffle(pool)
    items = pool[:total]
    questions = []
    for p in items:
        options = _make_options(p, total)
        questions.append({
            "indo": p["indo"],
            "jyutping": p.get("jyutping", ""),
            "options": options,
            "answer_index": options.index(p["yue"]),
        })
    return questions


def _make_options(correct, total: int = DEFAULT_TOTAL):
    """Cari pilihan asal (distractor) bagi soalan."""
    others = [p["yue"] for p in CURRICULUM
              if p.get("yue") and p["yue"] != correct]
    uniques = list(dict.fromkeys(o for o in others if o))
    count = min(total - 1, len(uniques))
    distractors = random.sample(uniques, count)
    options = distractors + [correct]
    random.shuffle(options)
    return options
