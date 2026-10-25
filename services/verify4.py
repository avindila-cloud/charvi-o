#!/usr/bin/env python3
"""Verify tkw_sentences_extended.py counts."""
import re

sv = "/c/Users/My OvoneL is Awesome/charvi-o/services"
extended_path = r"C:\Users\My OvoneL is Awesome\charvi-o\services\tkw_sentences_extended.py"

with open(extended_path, encoding="utf-8", errors="replace") as f:
    content = f.read()

# Handle Windows line endings
content = content.replace("\r\n", "\n")

categories = {}
current_cat = None
for line in content.split("\n"):
    stripped = line.strip()
    if stripped.startswith("# ---"):
        m = re.match(r"# --- (.+?) \((\d+)\) ---", stripped)
        if m:
            current_cat = m.group(1).strip()
            categories[current_cat] = []
    elif current_cat and stripped.startswith('"') and stripped.endswith('"'):
        s = stripped.strip().rstrip(",").strip()
        if s:
            categories[current_cat].append(s)

print("Current counts per category:")
for cat, sentences in sorted(categories.items(), key=lambda x: x[0]):
    print(f"  {cat}: {len(sentences)}")

total = sum(len(s) for s in categories.values())
print(f"\nTotal: {total}")
