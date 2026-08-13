"""
Nestly scraper — pulls live house listings (Title, Location, Beds/Baths, Price)
from nigeriapropertycentre.com and stores them via database/db.py.

IMPORTANT — read before running:
This sandbox's network is locked to package registries only, so this script
has NOT been run against the live site from here. The parsing logic below is
built from the site's actual page content (fetched via search), but real
estate sites tweak their markup often. Run this once locally / in Claude Code
where you have full internet, and if a field comes back empty, open DevTools
on a listing page and adjust the SELECTORS block below — everything else
stays the same.
"""
import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import insert_listings
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("SCRAPE_URL", "https://nigeriapropertycentre.com/for-rent/houses/showtype")
PAGES = int(os.getenv("SCRAPE_PAGES", 3))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# ---- Adjust these if the site's markup changes ----------------------------
SELECTORS = {
    "card": ["div.property-list", "div.wp-block", "article", "li.property"],
    "link_pattern": re.compile(r"/for-rent/houses/.*-\d{6,}[a-z0-9\-]*$|/\d{6,}-"),
    "price": [".property-price", ".price"],
    "location": [".property-location", ".location"],
    "beds": [".beds", ".fur-areas"],
}
# -----------------------------------------------------------------------------


def fetch_page(url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_listing_link(a_tag):
    """
    Given an <a> tag pointing at a listing detail page, walk up to the
    nearest card-like container and pull the fields out of its text.
    This text-pattern approach is more resilient to class-name churn
    than hard-coding a single CSS selector.
    """
    container = a_tag.find_parent(["article", "li", "div"])
    if container is None:
        return None

    text = container.get_text(" ", strip=True)

    title_tag = container.find(["h2", "h3", "h4"])
    title = title_tag.get_text(strip=True) if title_tag else None

    price_match = re.search(r"[N\u20a6][\d,]+(?:\.\d+)?\s*/?(?:yr|year|annum)?", text, re.I)
    price_raw = price_match.group(0) if price_match else None

    beds_match = re.search(r"(\d+)\s*Beds?", text, re.I)
    baths_match = re.search(r"(\d+)\s*Baths?", text, re.I)
    beds_raw = beds_match.group(0) if beds_match else None
    baths_raw = baths_match.group(0) if baths_match else None

    type_match = re.search(
        r"(Detached|Semi-detached|Terraced)\s+(Duplex|Bungalow)es?\s+for\s+rent", text, re.I
    )
    property_type = type_match.group(0) if type_match else None

    location = None
    if title:
        after_title = text.split(title, 1)[-1]
        loc_match = re.search(r"([A-Z][\w\s.'-]+,\s*[A-Z][\w\s.'-]+)", after_title)
        if loc_match:
            location = loc_match.group(1).strip()

    href = a_tag.get("href", "")
    source_url = href if href.startswith("http") else f"https://nigeriapropertycentre.com{href}"

    if not (title and price_raw):
        return None

    return {
        "title": title[:255],
        "location": (location or "Unknown")[:255],
        "price_raw": price_raw[:64],
        "beds_raw": (beds_raw or "")[:32],
        "baths_raw": (baths_raw or "")[:32],
        "property_type": (property_type or "")[:100],
        "source_url": source_url[:500],
    }


def scrape_page(url):
    soup = fetch_page(url)
    listing_links = [
        a for a in soup.find_all("a", href=True)
        if SELECTORS["link_pattern"].search(a["href"])
    ]

    seen_urls = set()
    results = []
    for a in listing_links:
        row = parse_listing_link(a)
        if row and row["source_url"] not in seen_urls:
            seen_urls.add(row["source_url"])
            results.append(row)
    return results


def run(pages=PAGES):
    all_rows = []
    for page in range(1, pages + 1):
        url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"
        print(f"Scraping page {page}: {url}")
        try:
            rows = scrape_page(url)
            print(f"  found {len(rows)} listings")
            all_rows.extend(rows)
        except requests.RequestException as e:
            print(f"  request failed: {e}")
        time.sleep(1.5)  # be polite

    if all_rows:
        inserted = insert_listings(all_rows)
        print(f"Saved/updated {inserted} rows in MongoDB.")
    else:
        print("No listings scraped — check SELECTORS in scrape.py against the live page.")
    return all_rows


if __name__ == "__main__":
    run()
