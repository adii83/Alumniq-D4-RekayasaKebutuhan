import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import fetch_data_dari_internet, hitung_bobot_kecocokan
import models
from urllib.parse import urlparse

# dummy alumni
alumni = models.Alumni(
    id=1,
    name="Marsel Putra Nugraha",
    campus="Universitas Muhammadiyah Malang",
    major="Informatika",
    source_platforms="LinkedIn, Google Scholar, GitHub"
)

# Test function
print("Fetching from internet...")
results = fetch_data_dari_internet('"Marsel Putra Nugraha" Universitas Muhammadiyah Malang')
print(f"Total results: {len(results)}")

for idx, res in enumerate(results):
    skor, match_nama = hitung_bobot_kecocokan(alumni, res)
    domain = urlparse(res.get("link", "")).netloc.lower()
    print(f"\n--- Result {idx+1} ---")
    print(f"Title: {res.get('sumber')}")
    print(f"URL: {res.get('link')}")
    print(f"Domain: {domain}")
    print(f"Snippet: {res.get('sinyal_pekerjaan')[:100]}")
    print(f"Score: M={match_nama}, T={skor}")

print("\nDone.")
