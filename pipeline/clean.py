"""
Pulls raw documents from MongoDB, cleans price/beds/baths with pandas,
scales price + beds with scikit-learn's StandardScaler, and writes the
cleaned + scaled values back onto the same documents.
"""
import os
import re
import sys

import pandas as pd
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import listings


def clean_price(raw):
    """'N25,000,000 /yr' -> 25000000. Handles N/₦, commas, and
    shorthand like '17M' or '1.2m' just in case."""
    if not raw:
        return None
    s = str(raw).upper().replace("₦", "")
    m_shorthand = re.search(r"([\d.]+)\s*M\b", s)
    if m_shorthand and "," not in s:
        return int(float(m_shorthand.group(1)) * 1_000_000)
    digits = re.sub(r"[^\d]", "", s.split("/")[0])
    return int(digits) if digits else None


def clean_int(raw):
    if not raw:
        return None
    m = re.search(r"\d+", str(raw))
    return int(m.group(0)) if m else None


def load_raw_df():
    docs = list(listings.find({}))
    return pd.DataFrame(docs)


def clean_and_scale(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["price_naira"] = df["price_raw"].apply(clean_price)
    df["beds"] = df["beds_raw"].apply(clean_int)
    df["baths"] = df["baths_raw"].apply(clean_int)

    before = len(df)
    df = df.dropna(subset=["price_naira", "beds"])
    df = df[(df["price_naira"] > 0) & (df["beds"] > 0)]
    print(f"Dropped {before - len(df)} rows with missing/invalid price or beds.")

    scaler = StandardScaler()
    df[["price_scaled", "beds_scaled"]] = scaler.fit_transform(df[["price_naira", "beds"]])

    return df


def save_clean(df: pd.DataFrame):
    updated = 0
    for _, row in df.iterrows():
        result = listings.update_one(
            {"_id": row["_id"]},
            {"$set": {
                "price_naira": int(row["price_naira"]),
                "beds": int(row["beds"]),
                "baths": None if pd.isna(row["baths"]) else int(row["baths"]),
                "price_scaled": float(row["price_scaled"]),
                "beds_scaled": float(row["beds_scaled"]),
            }},
        )
        updated += result.modified_count
    print(f"Updated {updated} documents with cleaned + scaled values.")


def run():
    raw = load_raw_df()
    print(f"Loaded {len(raw)} raw documents.")
    if raw.empty:
        print("No documents found — run a scraper/fetch script first.")
        return raw
    cleaned = clean_and_scale(raw)
    save_clean(cleaned)
    return cleaned


if __name__ == "__main__":
    result = run()
    if not result.empty:
        print(result[["title", "price_naira", "beds", "price_scaled", "beds_scaled"]].head(10))
