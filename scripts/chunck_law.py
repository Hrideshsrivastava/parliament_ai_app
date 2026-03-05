# scripts/chunk_law.py

import re
import json
import os

INPUT_PATH = "data/laws/Finance_Bill_2025.txt"
OUTPUT_PATH = "data/laws/finance_bill_chunks.json"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Match "Clause 87." or "87."
pattern = r"\n(?:Clause\s+)?(\d+)\.\s"
parts = re.split(pattern, text)

chunks = []

for i in range(1, len(parts), 2):
    clause_no = parts[i]
    clause_text = parts[i + 1].strip()

    if len(clause_text) < 50:
        continue  # skip junk

    chunks.append({
        "type": "law",
        "document": "Finance Bill 2025",
        "clause": clause_no,
        "text": clause_text,
        "source": "Finance Bill 2025 (as introduced)"
    })

os.makedirs("data/laws", exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print("Law chunks created:", len(chunks))
