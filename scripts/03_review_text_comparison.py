"""Compare common English words and phrases in low- and high-rated reviews."""

import csv
from collections import Counter
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np

from text_analysis_utils import review_terms


PROJECT_DIR = Path(__file__).resolve().parent.parent
REVIEW_FILE = PROJECT_DIR / "data" / "raw" / "All_Beauty.jsonl.gz"
REPORTS_DIR = PROJECT_DIR / "reports"
CHART_FILE = REPORTS_DIR / "02_review_terms_by_rating.png"
TABLE_FILE = REPORTS_DIR / "02_review_terms_by_rating.csv"
BATCH_SIZE = 10_000
MAX_TERMS = 20

def main() -> None:
    if not REVIEW_FILE.exists():
        raise FileNotFoundError(f"Missing data file: {REVIEW_FILE}. See README.md for download links.")

    connection = duckdb.connect(database=":memory:")
    try:
        cursor = connection.execute(
            f"""
            SELECT rating, text
            FROM read_json_auto('{str(REVIEW_FILE).replace("'", "''")}')
            WHERE rating IN (1, 2, 4, 5)
                AND text IS NOT NULL
                AND TRIM(text) != ''
            """
        )
        review_totals = Counter()
        term_counts = {"low": Counter(), "high": Counter()}

        while batch := cursor.fetchmany(BATCH_SIZE):
            for rating, text in batch:
                group = "low" if rating in (1, 2) else "high"
                review_totals[group] += 1
                term_counts[group].update(review_terms(text))
    finally:
        connection.close()

    if not review_totals["low"] or not review_totals["high"]:
        raise ValueError("Both low-rated and high-rated non-empty reviews are required.")

    minimum_low = max(100, int(review_totals["low"] * 0.001))
    minimum_high = max(100, int(review_totals["high"] * 0.001))
    candidates = set(term_counts["low"]) | set(term_counts["high"])
    comparison = []

    for term in candidates:
        low_count = term_counts["low"][term]
        high_count = term_counts["high"][term]
        if low_count < minimum_low and high_count < minimum_high:
            continue
        low_pct = low_count / review_totals["low"] * 100
        high_pct = high_count / review_totals["high"] * 100
        comparison.append(
            {
                "term": term,
                "low_review_count": low_count,
                "low_review_pct": round(low_pct, 3),
                "high_review_count": high_count,
                "high_review_pct": round(high_pct, 3),
                "high_minus_low_percentage_points": round(high_pct - low_pct, 3),
            }
        )

    comparison.sort(key=lambda row: abs(row["high_minus_low_percentage_points"]), reverse=True)
    top_terms = comparison[:MAX_TERMS]
    top_terms.sort(key=lambda row: row["high_minus_low_percentage_points"])

    REPORTS_DIR.mkdir(exist_ok=True)
    with TABLE_FILE.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(top_terms[0].keys()))
        writer.writeheader()
        writer.writerows(top_terms)

    labels = [row["term"] for row in top_terms]
    positions = np.arange(len(top_terms))
    bar_height = 0.36
    figure, axis = plt.subplots(figsize=(12, 9))
    axis.barh(
        positions - bar_height / 2,
        [row["low_review_pct"] for row in top_terms],
        bar_height,
        label="1–2 stars",
        color="#C45D45",
    )
    axis.barh(
        positions + bar_height / 2,
        [row["high_review_pct"] for row in top_terms],
        bar_height,
        label="4–5 stars",
        color="#2F7F6F",
    )
    axis.set_yticks(positions, labels)
    axis.invert_yaxis()
    axis.set_xlabel("Share of reviews mentioning the term (%)")
    axis.set_title("Common Words and Phrases by Review Rating", loc="left")
    axis.legend(frameon=False, ncols=2, loc="lower right")
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.grid(axis="x", color="#D9DEDC", linewidth=0.8)
    axis.set_axisbelow(True)
    figure.text(
        0.12,
        0.025,
        f"Low group: 1–2 stars (n={review_totals['low']:,}); high group: 4–5 stars (n={review_totals['high']:,}). 3-star reviews excluded.",
        fontsize=9,
        color="#4B5552",
    )
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    figure.savefig(CHART_FILE, dpi=180, bbox_inches="tight")
    plt.close(figure)

    print(f"Low-rated text reviews (1–2 stars): {review_totals['low']:,}")
    print(f"High-rated text reviews (4–5 stars): {review_totals['high']:,}")
    print(f"Saved chart: {CHART_FILE}")
    print(f"Saved term comparison table: {TABLE_FILE}")
    print("Note: this is a word/phrase frequency comparison, not an automated topic or causal analysis.")


if __name__ == "__main__":
    main()