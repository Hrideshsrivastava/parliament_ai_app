# scripts/parse_pdf.py

import pdfplumber
import os

PDF_DIR = "data/pdfs"
TEXT_DIR = "data/text"

os.makedirs(TEXT_DIR, exist_ok=True)

def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

for file in os.listdir(PDF_DIR):
    if not file.endswith(".pdf"):
        continue

    pdf_path = os.path.join(PDF_DIR, file)
    text = extract_text(pdf_path)

    txt_file = file.replace(".pdf", ".txt")
    out_path = os.path.join(TEXT_DIR, txt_file)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    print("Parsed:", txt_file)

print("All PDFs parsed to text.")
