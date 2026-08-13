"""
Nestly / Real Estate Price Predictor & Analyzer — MongoDB setup.

MongoDB is schemaless, so there's no CREATE TABLE step. This script just
sets up the one thing that matters structurally: a unique index on
source_url so re-running the scraper/dataset fetch upserts instead of
duplicating documents. db.py already calls create_index() on import, so
running this file directly is optional — it's here mainly as documentation
of the expected document shape.

Document shape (collection: "listings"):
{
    "_id":            ObjectId (auto),
    "title":          str,
    "location":       str,
    "price_raw":      str,   e.g. "N25,000,000 /yr"
    "beds_raw":       str,   e.g. "4 Beds"
    "baths_raw":      str,   e.g. "6 Baths"
    "property_type":  str,
    "source_url":     str,   unique
    "scraped_at":     datetime,

    # populated by pipeline/clean.py
    "price_naira":    int,
    "beds":           int,
    "baths":          int,
    "price_scaled":   float,   # StandardScaler output
    "beds_scaled":    float,   # StandardScaler output
}

Run: python3 database/setup_indexes.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import listings

if __name__ == "__main__":
    listings.create_index("source_url", unique=True, sparse=True)
    print("Index ready on 'source_url'.")
    print("Existing document count:", listings.count_documents({}))
