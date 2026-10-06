"""Plot one- and five-star review counts for the ten most-reviewed products."""

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
REPORTS_DIR = PROJECT_DIR / "reports"
REVIEW_FILE = RAW_DIR / "All_Beauty.jsonl.gz"
PRODUCT_FILE = RAW_DIR / "meta_All_Beauty.jsonl.gz"
OUTPUT_FILE = REPORTS_DIR / "01_product_star_counts.png"
TABLE_FILE = REPORTS_DIR / "01_product_star_counts.csv"


def sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def main() -> None:
    missing = [path.name for path in (REVIEW_FILE, PRODUCT_FILE) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing data file(s): {', '.join(missing)}. See README.md for download links."
        )

    connection = duckdb.connect(database=":memory:")
    try:
        results = connection.execute(
            f"""
            WITH review_summary AS (
                SELECT
                    parent_asin,
                    COUNT(*) AS review_count,
                    COUNT(*) FILTER (WHERE rating = 1) AS one_star_count,
                    COUNT(*) FILTER (WHERE rating = 5) AS five_star_count
                FROM read_json_auto('{sql_path(REVIEW_FILE)}')
                WHERE parent_asin IS NOT NULL
                    AND rating BETWEEN 1 AND 5
                    AND rating = FLOOR(rating)
                GROUP BY parent_asin
            ), product_titles AS (
                SELECT parent_asin, ANY_VALUE(title) AS product_title
                FROM read_json_auto('{sql_path(PRODUCT_FILE)}')
                GROUP BY parent_asin
            )
            SELECT
                review_summary.parent_asin,
                COALESCE(NULLIF(TRIM(product_titles.product_title), ''), review_summary.parent_asin)
                    AS product_title,
                review_count,
                one_star_count,
                five_star_count
            FROM review_summary
            LEFT JOIN product_titles USING (parent_asin)
            ORDER BY review_count DESC
            LIMIT 10
            """
        ).df()
    finally:
        connection.close()

    if results.empty:
        raise ValueError("No products with valid ratings and product IDs were found.")

    results["one_star_pct"] = (results["one_star_count"] / results["review_count"] * 100).round(2)
    results["five_star_pct"] = (results["five_star_count"] / results["review_count"] * 100).round(2)
    results["short_title"] = results["product_title"].str.slice(0, 48).str.rstrip()
    positions = np.arange(len(results))
    bar_height = 0.36

    figure, axis = plt.subplots(figsize=(13, 8))
    one_star_bars = axis.barh(
        positions - bar_height / 2,
        results["one_star_count"],
        bar_height,
        label="1 star",
        color="#C45D45",
    )
    five_star_bars = axis.barh(
        positions + bar_height / 2,
        results["five_star_count"],
        bar_height,
        label="5 stars",
        color="#2F7F6F",
    )

    largest_bar = max(results["one_star_count"].max(), results["five_star_count"].max())
    axis.set_xlim(0, largest_bar * 1.55 if largest_bar else 1)
    for bars, counts in (
        (one_star_bars, results["one_star_count"]),
        (five_star_bars, results["five_star_count"]),
    ):
        for bar, count, total in zip(bars, counts, results["review_count"]):
            percentage = count / total * 100
            axis.text(
                bar.get_width() + largest_bar * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{count:,} ({percentage:.1f}%)",
                va="center",
                fontsize=9,
            )

    axis.set_yticks(positions, results["short_title"])
    axis.invert_yaxis()
    axis.set_xlabel("Number of reviews")
    axis.set_title("One- and Five-Star Reviews for the 10 Most-Reviewed Products", loc="left")
    axis.legend(frameon=False, ncols=2, loc="lower right")
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.grid(axis="x", color="#D9DEDC", linewidth=0.8)
    axis.set_axisbelow(True)
    figure.text(
        0.12,
        0.025,
        "Labels show count and share of each product's reviews. Review count is not sales.",
        fontsize=9,
        color="#4B5552",
    )
    figure.tight_layout(rect=(0, 0.06, 1, 1))

    REPORTS_DIR.mkdir(exist_ok=True)
    figure.savefig(OUTPUT_FILE, dpi=180, bbox_inches="tight")
    results.to_csv(TABLE_FILE, index=False)
    print(f"Saved chart: {OUTPUT_FILE}")
    print(f"Saved data table: {TABLE_FILE}")
    print(
        results[
            ["parent_asin", "review_count", "one_star_count", "one_star_pct", "five_star_count", "five_star_pct"]
        ].to_string(index=False)
    )
    plt.close(figure)


if __name__ == "__main__":
    main()