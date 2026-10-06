"""Compare review phrases by rating for selected high-review beauty products."""

import csv
from collections import Counter
from math import ceil
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np

from text_analysis_utils import review_terms


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
REPORTS_DIR = PROJECT_DIR / "reports"
REVIEW_FILE = RAW_DIR / "All_Beauty.jsonl.gz"
PRODUCT_FILE = RAW_DIR / "meta_All_Beauty.jsonl.gz"
CHART_FILE = REPORTS_DIR / "03_selected_product_phrase_comparison.png"
TABLE_FILE = REPORTS_DIR / "03_selected_product_phrase_comparison.csv"
PRODUCT_IDS = [
    "B085BB7B1M",
    "B0BM4GX6TT",
    "B00R1TAN7I",
    "B019GBG0IE",
    "B01M1OFZOG",
]
BATCH_SIZE = 5_000
PHRASES_PER_PRODUCT = 6


def sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def main() -> None:
    missing = [path.name for path in (REVIEW_FILE, PRODUCT_FILE) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing data file(s): {', '.join(missing)}. See README.md for download links."
        )

    placeholders = ", ".join("?" for _ in PRODUCT_IDS)
    connection = duckdb.connect(database=":memory:")
    try:
        titles = dict(
            connection.execute(
                f"""
                SELECT parent_asin, ANY_VALUE(title)
                FROM read_json_auto('{sql_path(PRODUCT_FILE)}')
                WHERE parent_asin IN ({placeholders})
                GROUP BY parent_asin
                """,
                PRODUCT_IDS,
            ).fetchall()
        )
        cursor = connection.execute(
            f"""
            SELECT parent_asin, rating, text
            FROM read_json_auto('{sql_path(REVIEW_FILE)}')
            WHERE parent_asin IN ({placeholders})
                AND rating IN (1, 2, 4, 5)
                AND text IS NOT NULL
                AND TRIM(text) != ''
            """,
            PRODUCT_IDS,
        )
        review_totals = {product_id: Counter() for product_id in PRODUCT_IDS}
        phrase_counts = {
            product_id: {"low": Counter(), "high": Counter()}
            for product_id in PRODUCT_IDS
        }

        while batch := cursor.fetchmany(BATCH_SIZE):
            for product_id, rating, text in batch:
                group = "low" if rating in (1, 2) else "high"
                review_totals[product_id][group] += 1
                phrase_counts[product_id][group].update(review_terms(text, phrases_only=True))
    finally:
        connection.close()

    rows = []
    plot_data = []
    for product_id in PRODUCT_IDS:
        low_total = review_totals[product_id]["low"]
        high_total = review_totals[product_id]["high"]
        if not low_total or not high_total:
            raise ValueError(f"Both rating groups are required for {product_id}.")

        low_minimum = max(5, ceil(low_total * 0.01))
        high_minimum = max(5, ceil(high_total * 0.01))
        candidates = set(phrase_counts[product_id]["low"]) | set(phrase_counts[product_id]["high"])
        product_rows = []

        for phrase in candidates:
            low_count = phrase_counts[product_id]["low"][phrase]
            high_count = phrase_counts[product_id]["high"][phrase]
            if low_count < low_minimum and high_count < high_minimum:
                continue
            low_pct = low_count / low_total * 100
            high_pct = high_count / high_total * 100
            product_rows.append(
                {
                    "parent_asin": product_id,
                    "product_title": titles.get(product_id) or product_id,
                    "low_review_total": low_total,
                    "high_review_total": high_total,
                    "phrase": phrase,
                    "low_review_count": low_count,
                    "low_review_pct": round(low_pct, 3),
                    "high_review_count": high_count,
                    "high_review_pct": round(high_pct, 3),
                    "high_minus_low_percentage_points": round(high_pct - low_pct, 3),
                }
            )

        product_rows.sort(
            key=lambda row: abs(row["high_minus_low_percentage_points"]), reverse=True
        )
        selected = product_rows[:PHRASES_PER_PRODUCT]
        if not selected:
            raise ValueError(f"No frequent two-word phrases were found for {product_id}.")
        selected.sort(key=lambda row: row["high_minus_low_percentage_points"])
        rows.extend(selected)
        plot_data.append((product_id, selected))

    REPORTS_DIR.mkdir(exist_ok=True)
    with TABLE_FILE.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    figure, axes = plt.subplots(len(PRODUCT_IDS), 1, figsize=(14, 19), sharex=True)
    maximum_percentage = max(
        max(row["low_review_pct"], row["high_review_pct"])
        for row in rows
    )
    for axis, (product_id, product_rows) in zip(axes, plot_data):
        labels = [row["phrase"] for row in product_rows]
        positions = np.arange(len(product_rows))
        bar_height = 0.36
        axis.barh(
            positions - bar_height / 2,
            [row["low_review_pct"] for row in product_rows],
            bar_height,
            label="1–2 stars",
            color="#C45D45",
        )
        axis.barh(
            positions + bar_height / 2,
            [row["high_review_pct"] for row in product_rows],
            bar_height,
            label="4–5 stars",
            color="#2F7F6F",
        )
        axis.set_yticks(positions, labels)
        axis.invert_yaxis()
        axis.set_xlim(0, maximum_percentage * 1.15)
        axis.set_title(
            f"{(titles.get(product_id) or product_id)[:72]}  |  "
            f"1–2 stars: n={review_totals[product_id]['low']:,}; "
            f"4–5 stars: n={review_totals[product_id]['high']:,}",
            loc="left",
            fontsize=11,
        )
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.grid(axis="x", color="#D9DEDC", linewidth=0.8)
        axis.set_axisbelow(True)

    axes[-1].set_xlabel("Share of the product's reviews mentioning the phrase (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, frameon=False, ncols=2, loc="upper right")
    figure.suptitle("Review Phrases by Rating Within Selected Products", x=0.08, ha="left", fontsize=16)
    figure.text(
        0.08,
        0.01,
        "Products selected from the most-reviewed list based on title relevance. "
        "Only 1–2 and 4–5 star reviews are included; each phrase is counted once per review.",
        fontsize=9,
        color="#4B5552",
    )
    figure.tight_layout(rect=(0, 0.035, 1, 0.97))
    figure.savefig(CHART_FILE, dpi=180, bbox_inches="tight")
    plt.close(figure)

    for product_id in PRODUCT_IDS:
        print(
            f"{product_id}: low-rating reviews={review_totals[product_id]['low']:,}, "
            f"high-rating reviews={review_totals[product_id]['high']:,}"
        )
    print(f"Saved chart: {CHART_FILE}")
    print(f"Saved phrase comparison table: {TABLE_FILE}")
    print("Note: phrases indicate association with rating groups, not causes of ratings.")


if __name__ == "__main__":
    main()