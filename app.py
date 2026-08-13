"""
Nestly Flask dashboard.
Shows the current listings table plus the two required charts
(scatter: beds vs price, bar: avg price by location).
"""
import os
import subprocess
import sys

from flask import Flask, render_template, redirect, url_for, flash

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db import listings

app = Flask(__name__)
app.secret_key = "dev-only-secret-change-me"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_listings(limit=60):
    return list(
        listings.find(
            {"price_naira": {"$ne": None}},
            {"title": 1, "location": 1, "price_naira": 1, "beds": 1,
             "baths": 1, "property_type": 1, "source_url": 1},
        ).sort("price_naira", -1).limit(limit)
    )


def fetch_stats():
    prices = [
        doc["price_naira"]
        for doc in listings.find({"price_naira": {"$ne": None}}, {"price_naira": 1})
    ]
    if not prices:
        return {"total": 0, "avg_price": None, "min_price": None, "max_price": None}
    return {
        "total": len(prices),
        "avg_price": sum(prices) / len(prices),
        "min_price": min(prices),
        "max_price": max(prices),
    }


@app.route("/")
def dashboard():
    listings = fetch_listings()
    stats = fetch_stats()
    charts_exist = os.path.exists(os.path.join(BASE_DIR, "static", "charts", "scatter_beds_price.png"))
    return render_template("dashboard.html", listings=listings, stats=stats, charts_exist=charts_exist)


@app.route("/refresh", methods=["POST"])
def refresh():
    """Re-run clean + visualize against whatever's currently in MongoDB
    (run scraper/scrape.py separately to pull fresh listings first)."""
    try:
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "pipeline", "clean.py")], check=True)
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "pipeline", "visualize.py")], check=True)
        flash("Data cleaned and charts refreshed.", "success")
    except subprocess.CalledProcessError:
        flash("Refresh failed — check the server logs.", "error")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
