"""
Nestly — SAFE data source.

Instead of scraping a commercial listing site's HTML (gray-area under most
sites' Terms of Service), this pulls a public dataset already published on
GitHub: ~49,800 real Lagos rental listings (price, beds, baths, neighborhood),
originally compiled from propertypro.ng and shared openly for ML practice by
its author (PE-Ibeabcuhi/Lagos-Rent-Prediction).

Why this is the safer choice:
- It's a direct file download (like clicking "Download" in a browser),
  not automated crawling of a live commercial site.
- Raw factual data (price, bed/bath counts) isn't the kind of thing
  copyright protects — it's numbers, not creative writing.
- No ToS is being bypassed, no login wall crossed, no server hammered
  with repeated requests.
This still satisfies the assignment's "pull external data with requests
+ store in MongoDB + clean with pandas" requirement — it just swaps *where*
the raw data comes from.

Run: python3 scraper/fetch_dataset.py
"""
import os
import sys
import tempfile

import pandas as pd
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import insert_listings

DATASET_URL = (
    "https://raw.githubusercontent.com/PE-Ibeabcuhi/"
    "Lagos-Rent-Prediction/main/Cleaned_lagos_renewed.csv"
)

# Keep the demo/dashboard snappy — bump this up if you want the full set.
SAMPLE_SIZE = 400


def download():
    resp = requests.get(DATASET_URL, timeout=30)
    resp.raise_for_status()
    path = os.path.join(tempfile.gettempdir(), "lagos_rent.csv")
    with open(path, "wb") as f:
        f.write(resp.content)
    return path


def to_rows(df: pd.DataFrame):
    rows = []
    for i, r in df.iterrows():
        beds = int(r["Bedrooms"]) if pd.notna(r["Bedrooms"]) else None
        baths = int(r["Bathrooms"]) if pd.notna(r["Bathrooms"]) else None
        price = int(r["Price"]) if pd.notna(r["Price"]) else None
        neighborhood = str(r["Neighborhood"]).strip() if pd.notna(r["Neighborhood"]) else "Unknown"
        if price is None or beds is None:
            continue

        tags = []
        if r.get("Serviced") == 1:
            tags.append("Serviced")
        if r.get("Newly Built") == 1:
            tags.append("Newly Built")
        if r.get("Furnished") == 1:
            tags.append("Furnished")
        property_type = ", ".join(tags) if tags else "Standard"

        rows.append({
            "title": f"{beds} Bedroom Flat in {neighborhood}",
            "location": f"{neighborhood}, Lagos",
            "price_raw": f"N{price:,} /yr",
            "beds_raw": f"{beds} Beds",
            "baths_raw": f"{baths} Baths" if baths else "",
            "property_type": property_type[:100],
            "source_url": f"dataset-row-{i}",
        })
    return rows


def run(sample_size=SAMPLE_SIZE):
    print(f"Downloading dataset from {DATASET_URL} ...")
    path = download()
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} total rows from the public dataset.")

    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
        print(f"Sampling {sample_size} rows for the demo dashboard.")

    rows = to_rows(df)
    inserted = insert_listings(rows)
    print(f"Saved/updated {inserted} rows in MongoDB.")
    return rows


if __name__ == "__main__":
    run()
