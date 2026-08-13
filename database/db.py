"""
Shared MongoDB connection helper for Nestly.
Every other module (scraper, pipeline, app) imports from here instead of
opening its own connection.

For real use: set MONGO_URI in .env to point at your MongoDB instance
(local `mongod`, or a free Atlas cluster — see README).

USE_MOCK_DB=1 is a sandbox/dev-only convenience: it swaps in `montydb`
(a disk-persisted, embedded MongoDB-compatible engine) so the pipeline is
fully testable without a real `mongod` server installed. Leave it unset
for your actual project — it should talk to a real MongoDB.
"""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

USE_MOCK = os.getenv("USE_MOCK_DB") == "1"

if USE_MOCK:
    from montydb import MontyClient, set_storage
    _storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".monty_data")
    set_storage(_storage_path, storage="sqlite")
    _client = MontyClient(_storage_path)
else:
    from pymongo import MongoClient
    _client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))

_db = _client[os.getenv("MONGO_DB", "nestly")]
listings = _db[os.getenv("MONGO_COLLECTION", "listings")]

# Unique index on source_url — re-running the scraper/dataset fetch is
# safe, it upserts instead of duplicating (mirrors the old MySQL UNIQUE KEY).
listings.create_index("source_url", unique=True, sparse=True)


def get_collection():
    return listings


def insert_listings(rows):
    """
    rows: list of dicts with keys
    title, location, price_raw, beds_raw, baths_raw, property_type, source_url
    Upserts on source_url so re-running the scraper/dataset fetch just
    refreshes existing documents instead of duplicating them.
    """
    if not rows:
        return 0

    count = 0
    for row in rows:
        row = dict(row)
        row["scraped_at"] = datetime.now(timezone.utc)
        result = listings.update_one(
            {"source_url": row["source_url"]},
            {"$set": row},
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            count += 1
    return count


if __name__ == "__main__":
    print("Connected OK. Backend:", "montydb (sandbox test mode)" if USE_MOCK else "real MongoDB")
    print("Document count:", listings.count_documents({}))
