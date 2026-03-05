import pdfplumber
import os

PDF_PATH = "data/laws/Finance_Bill.pdf"
OUT_PATH = "data/laws/Finance_Bill_2025.txt"

text = ""
with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(text)

print("Finance Bill text extracted.")
