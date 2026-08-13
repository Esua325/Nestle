# Nestly — Real Estate Price Predictor & Analyzer

Aptech Final Capstone (Project Code VE). Pulls house listing data,
stores it in MongoDB, cleans + scales it with pandas/scikit-learn,
builds two charts, and serves it all through a Flask dashboard.

## Stack
- **Data source**: public GitHub dataset (safe, no scraping-legality questions) with an optional live-scraper as a stretch option
- **Database**: MongoDB
- **Cleaning / ML prep**: `pandas`, `scikit-learn` (`StandardScaler`)
- **Visualization**: `matplotlib` — scatter (Beds vs Price) + bar (Avg price per Location)
- **App**: Flask

## About the data source — read this first

The assignment asks you to scrape a live listings site, but scraping a
commercial real estate site's HTML sits in a legal gray area (it usually
violates their Terms of Service, even though the data itself is public).
For a school project, the realistic risk is very low, but there's a
genuinely safer option that still satisfies the "pull external data with
code + store in MongoDB + clean with pandas" requirement:

**`scraper/fetch_dataset.py`** (recommended, default) downloads a public
dataset of ~49,800 real Lagos rental listings from a GitHub repo
(originally compiled from propertypro.ng by another student for an ML
project, and shared openly). This is a plain file download — no bypassing
a login, no ignoring a site's Terms of Service, no repeated automated hits
against someone's live servers. Mention this swap in your defense: it's a
legitimate engineering call, not a shortcut.

**`scraper/scrape.py`** (optional, stretch goal) is the live HTML scraper
against nigeriapropertycentre.com, built from the site's real page
structure. If you want the "true" live-scraping version for extra marks,
this is there — just be aware it's untested from this sandbox (see the
note at the top of that file) and carries the ToS caveat above.

## Project layout
```
nestly-app/
├── app.py                     # Flask app + dashboard route
├── requirements.txt
├── .env                       # DB config + scrape config
├── database/
│   ├── setup_indexes.py       # creates the unique index on source_url
│   └── db.py                  # connection + insert helper (PyMongo)
├── scraper/
│   ├── fetch_dataset.py       # SAFE: pulls public GitHub dataset (recommended)
│   ├── scrape.py              # optional: live scraper (run with real internet access)
│   └── seed_data.py           # small hand-picked sample, for a quick sanity check
├── pipeline/
│   ├── clean.py                # pandas cleaning + StandardScaler
│   └── visualize.py           # builds the two required charts
├── templates/
│   └── dashboard.html
└── static/
    ├── css/style.css
    ├── img/                   # brand ornaments (vines, fret marks)
    └── charts/                # generated PNGs land here
```

## Setup

1. **Get MongoDB running.** Easiest options:
   - **Local install**: download MongoDB Community Server from
     mongodb.com/try/download/community, install it, and make sure the
     `mongod` service is running (`mongodb://localhost:27017` by default).
   - **Free cloud option (no install)**: create a free MongoDB Atlas
     cluster at mongodb.com/atlas, and grab its connection string.

2. **Update `.env`** with your connection details:
   ```
   MONGO_URI=mongodb://localhost:27017
   MONGO_DB=nestly
   MONGO_COLLECTION=listings
   USE_MOCK_DB=0
   ```
   For Atlas, `MONGO_URI` will look like
   `mongodb+srv://user:password@cluster.mongodb.net`.

3. **Install Python dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Create the index** (optional — `db.py` also does this automatically
   on first connect):
   ```bash
   python3 database/setup_indexes.py
   ```

5. **Get data in.** Recommended:
   ```bash
   python3 scraper/fetch_dataset.py
   ```
   Pulls ~400 real Lagos listings (sampled from a public 49,800-row GitHub
   dataset) straight into MongoDB — no scraping-legality questions, see above.

   Other options:
   - **Tiny sanity check**: `python3 scraper/seed_data.py` — 22 hand-picked
     sample listings if you just want to confirm the pipeline runs.
   - **Live scrape (optional/advanced)**: `python3 scraper/scrape.py` — pulls
     current listings directly from nigeriapropertycentre.com. Read the note
     at the top of that file first — the selectors were built from the
     site's real content but couldn't be tested live from this sandboxed
     environment (no general internet access here). If a run comes back
     with 0 listings, open a listing page in your browser's DevTools and
     adjust the `SELECTORS` block — the surrounding scraping/parsing/
     pagination logic doesn't need to change.

6. **Run the pipeline**:
   ```bash
   python3 pipeline/clean.py       # cleans price/beds/baths, applies StandardScaler
   python3 pipeline/visualize.py   # builds the two charts into static/charts/
   ```

7. **Launch the dashboard**:
   ```bash
   python3 app.py
   ```
   Visit http://localhost:5000 — you'll see summary stats, both charts, and
   the full listings table. The **Refresh charts** button re-runs clean +
   visualize against whatever's currently in MongoDB (run the scraper first
   to get fresh rows).

## A note on how this was built and tested

This project was developed in a sandboxed environment that couldn't
install a real `mongod` server (MongoDB was dropped from Ubuntu's official
package repos, and MongoDB's own repo wasn't reachable from there). So the
full pipeline — data fetch, cleaning, scaling, charts, and the Flask
dashboard — was tested end-to-end against `montydb`, a disk-persisted,
MongoDB-API-compatible embedded database, enabled by setting
`USE_MOCK_DB=1` in `.env`.

**For your real setup, leave `USE_MOCK_DB=0`** (or unset) so `database/db.py`
connects to an actual MongoDB via `MONGO_URI`. The application code is
identical either way — only the connection target changes. `mongomock` and
`montydb` are listed in `requirements.txt` purely as this dev/test
convenience; they're not needed for the real deployment, though there's no
harm leaving them installed.

## Notes for the write-up / defense
- `price_naira`, `beds`, `baths` are the **cleaned** numeric fields;
  `price_raw` / `beds_raw` / `baths_raw` keep the original text
  for reference.
- `price_scaled` / `beds_scaled` are the `StandardScaler` output fields —
  useful if you extend this into the ML price-prediction bonus feature.
- Re-running the fetch/scraper is safe — `source_url` is a unique index,
  so repeat runs upsert instead of duplicating documents.
- Bonus features from the assignment (login, PDF export, ML prediction,
  live deployment, API integration) aren't built yet — this covers the
  base 70-mark technical layer end to end.
