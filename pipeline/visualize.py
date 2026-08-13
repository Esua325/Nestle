"""
Builds the two required charts:
  1. Scatter plot: Beds vs Price
  2. Bar chart: Average price per Location
Saved as PNGs into static/charts/ so Flask can serve them directly.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import listings

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "charts")
os.makedirs(OUT_DIR, exist_ok=True)

# Nestly brand palette
MOSS = "#35503D"
GOLD = "#B8933E"
PARCHMENT = "#F1EAD9"
CHARCOAL = "#2A2620"


def load_df():
    docs = list(listings.find(
        {"price_naira": {"$ne": None}, "beds": {"$ne": None}},
        {"title": 1, "location": 1, "price_naira": 1, "beds": 1, "baths": 1},
    ))
    return pd.DataFrame(docs)


def style_axes(ax):
    ax.set_facecolor(PARCHMENT)
    ax.figure.set_facecolor(PARCHMENT)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(CHARCOAL)
    ax.tick_params(colors=CHARCOAL)
    ax.xaxis.label.set_color(CHARCOAL)
    ax.yaxis.label.set_color(CHARCOAL)
    ax.title.set_color(CHARCOAL)


def scatter_beds_vs_price(df):
    fig, ax = plt.subplots(figsize=(7, 5), dpi=140)
    ax.scatter(df["beds"], df["price_naira"] / 1_000_000, color=MOSS, s=90,
               edgecolors=GOLD, linewidths=1.2, alpha=0.85)
    ax.set_xlabel("Bedrooms")
    ax.set_ylabel("Price (\u20a6 millions/yr)")
    ax.set_title("Beds vs Price")
    style_axes(ax)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "scatter_beds_price.png")
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def bar_avg_price_by_location(df, top_n=10):
    # Group by the last two comma-separated segments (area, city) to
    # avoid every unique street address becoming its own bar.
    df = df.copy()
    df["area"] = df["location"].apply(
        lambda loc: ",".join([p.strip() for p in loc.split(",")[-2:]]) if "," in loc else loc
    )
    avg = (
        df.groupby("area")["price_naira"]
        .mean()
        .div(1_000_000)
        .sort_values(ascending=False)
        .head(top_n)
    )

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=140)
    bars = ax.barh(avg.index[::-1], avg.values[::-1], color=MOSS)
    for bar, val in zip(bars, avg.values[::-1]):
        ax.text(bar.get_width() + max(avg.values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"\u20a6{val:,.1f}M", va="center", color=CHARCOAL, fontsize=9)
    ax.set_xlabel("Average price (\u20a6 millions/yr)")
    ax.set_title(f"Average Price by Location (top {top_n})")
    style_axes(ax)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "bar_avg_price_location.png")
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def run():
    df = load_df()
    if df.empty:
        print("No cleaned rows found — run pipeline/clean.py first.")
        return
    p1 = scatter_beds_vs_price(df)
    p2 = bar_avg_price_by_location(df)
    print("Wrote:", p1)
    print("Wrote:", p2)


if __name__ == "__main__":
    run()
