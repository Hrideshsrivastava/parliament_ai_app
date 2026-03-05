# scripts/fetch_handles.py

import requests
import time
from bs4 import BeautifulSoup

BASE = "https://eparlib.sansad.in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml"
}

START = 0
STEP = 20
all_handles = set()

while True:
    url = (
        f"{BASE}/handle/123456789/7/simple-search"
        f"?query=&filter_field_1=title"
        f"&filter_type_1=equals"
        f"&filter_value_1=Lok+Sabha+Debates"
        f"&sort_by=dc.date_dt&order=desc"
        f"&rpp={STEP}&etal=0&start={START}"
    )

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "lxml")

    table = soup.select_one("table.table-hover")
    if not table:
        break

    page_handles = set()
    for a in table.select('a[href^="/handle/123456789/"]'):
        href = a["href"].split("?")[0]
        page_handles.add(BASE + href)

    new_handles = page_handles - all_handles
    if not new_handles:
        break

    all_handles.update(new_handles)
    print(f"Added {len(new_handles)} handles (total {len(all_handles)})")

    START += STEP
    if START>=100 :
        break
    time.sleep(1)


# SAVE TO FILE
with open("data/handles.txt", "w") as f:
    for h in sorted(all_handles):
        f.write(h + "\n")

print("FINAL HANDLE COUNT:", len(all_handles))
print("Saved to data/handles.txt")
