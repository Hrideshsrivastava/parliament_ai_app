# scripts/fetch_pdfs.py

import requests
import time
import os
from bs4 import BeautifulSoup

BASE = "https://eparlib.sansad.in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml"
}

PDF_DIR = "data/pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

# LOAD HANDLES
with open("data/handles.txt", "r") as f:
    handles = [line.strip() for line in f if line.strip()]

print("Handles loaded:", len(handles))

for handle in handles:
    r = requests.get(handle, headers=HEADERS)
    soup = BeautifulSoup(r.text, "lxml")

    pdf = soup.select_one('a[href^="/bitstream/"][href$=".pdf"]')
    if not pdf:
        continue

    pdf_url = BASE + pdf["href"]
    filename = pdf_url.split("/")[-1]
    filepath = os.path.join(PDF_DIR, filename)

    if os.path.exists(filepath):
        continue

    print("Downloading:", filename)
    data = requests.get(pdf_url, headers=HEADERS).content

    with open(filepath, "wb") as f:
        f.write(data)

    time.sleep(1)

print("PDF download complete.")
