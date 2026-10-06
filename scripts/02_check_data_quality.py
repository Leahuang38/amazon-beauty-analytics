"""Check missing values, rating validity, duplicate candidates, and join coverage."""

import csv
from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
REPORTS_DIR = PROJECT_DIR / "reports"
REVIEW_FILE = RAW_DIR / "All_Beauty.jsonl.gz"
PRODUCT_FILE = RAW_DIR / "meta_All_Beauty.jsonl.gz"
OUTPUT_FILE = REPORTS_DIR / "00_data_quality.csv"

REVIEW_FIELDS = ["rating", "parent_asin", "text", "title", "timestamp", "helpful_vote"]
PRODUCT_FIELDS = ["parent_asin", "title", "main_category", "price", "store", "categories"]


def sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def add_metric(rows: list[dict[str, object]], section: str, name: str, value: int,
               total: int | None = None) -> None:
    percentage = round(value / total * 100, 2) if total else ""
    rows.append({"section": section, "check": name, "value": value, "percent": percentage})


def main() -> None:
    missing_files = [path.name for path in (REVIEW_FILE, PRODUCT_FILE) if not path.exists()]
    if missing_files:
        raise FileNotFoundError(
            f"Missing data file(s): {', '.join(missing_files)}. See README.md for download links."
        )

    connection = duckdb.connect(database=":memory:")
    try:
        review_path = sql_path(REVIEW_FILE)
        product_path = sql_path(PRODUCT_FILE)

        review = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT parent_asin) AS distinct_product_ids,
                COUNT(*) FILTER (WHERE rating IS NOT NULL AND (rating < 1 OR rating > 5))
                    AS out_of_range_ratings,
                COUNT(*) FILTER (WHERE rating IS NOT NULL AND rating != FLOOR(rating))
                    AS non_integer_ratings,
                COUNT(*) FILTER (WHERE text IS NOT NULL AND TRIM(text) = '') AS blank_text,
                COUNT(*) - COUNT(DISTINCT (
                    parent_asin, user_id, timestamp, rating, title, text
                )) AS repeated_core_review_rows
            FROM read_json_auto('{review_path}')
            """
        ).fetchone()
        product = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT parent_asin) AS distinct_product_ids,
                COUNT(*) FILTER (WHERE parent_asin IS NULL) AS missing_product_ids,
                COUNT(*) - COUNT(DISTINCT parent_asin) AS repeated_product_id_rows
            FROM read_json_auto('{product_path}')
            """
        ).fetchone()

        review_missing = connection.execute(
            f"""
            SELECT
                {', '.join(f'COUNT(*) FILTER (WHERE {field} IS NULL)' for field in REVIEW_FIELDS)}
            FROM read_json_auto('{review_path}')
            """
        ).fetchone()
        product_missing = connection.execute(
            f"""
            SELECT
                {', '.join(f'COUNT(*) FILTER (WHERE {field} IS NULL)' for field in PRODUCT_FIELDS)}
            FROM read_json_auto('{product_path}')
            """
        ).fetchone()

        join_coverage = connection.execute(
            f"""
            WITH review_ids AS (
                SELECT DISTINCT parent_asin
                FROM read_json_auto('{review_path}')
                WHERE parent_asin IS NOT NULL
            ), product_ids AS (
                SELECT DISTINCT parent_asin
                FROM read_json_auto('{product_path}')
                WHERE parent_asin IS NOT NULL
            )
            SELECT
                COUNT(*) AS review_product_ids,
                COUNT(*) FILTER (WHERE product_ids.parent_asin IS NOT NULL) AS matched_ids
            FROM review_ids
            LEFT JOIN product_ids USING (parent_asin)
            """
        ).fetchone()
    finally:
        connection.close()

    review_total, review_distinct_ids, out_of_range_ratings, non_integer_ratings, blank_text, repeated_core = review
    product_total, product_distinct_ids, missing_product_ids, repeated_product_ids = product
    review_product_ids, matched_ids = join_coverage

    rows: list[dict[str, object]] = []
    add_metric(rows, "reviews", "total rows", review_total)
    add_metric(rows, "reviews", "distinct non-null parent_asin", review_distinct_ids)
    add_metric(rows, "reviews", "ratings outside 1-5", out_of_range_ratings, review_total)
    add_metric(rows, "reviews", "non-integer ratings", non_integer_ratings, review_total)
    add_metric(rows, "reviews", "blank review text", blank_text, review_total)
    add_metric(rows, "reviews", "repeated core review rows (candidate)", repeated_core, review_total)
    for field, count in zip(REVIEW_FIELDS, review_missing):
        add_metric(rows, "reviews", f"missing {field}", count, review_total)

    add_metric(rows, "products", "total rows", product_total)
    add_metric(rows, "products", "distinct non-null parent_asin", product_distinct_ids)
    add_metric(rows, "products", "missing parent_asin", missing_product_ids, product_total)
    add_metric(rows, "products", "repeated parent_asin rows", repeated_product_ids, product_total)
    for field, count in zip(PRODUCT_FIELDS, product_missing):
        add_metric(rows, "products", f"missing {field}", count, product_total)

    match_percentage = round(matched_ids / review_product_ids * 100, 2) if review_product_ids else 0
    rows.extend(
        [
            {"section": "join", "check": "distinct review product IDs", "value": review_product_ids, "percent": ""},
            {"section": "join", "check": "matched product IDs", "value": matched_ids, "percent": match_percentage},
            {"section": "join", "check": "unmatched product IDs", "value": review_product_ids - matched_ids, "percent": round(100 - match_percentage, 2)},
        ]
    )

    REPORTS_DIR.mkdir(exist_ok=True)
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=["section", "check", "value", "percent"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Reviews: {review_total:,} rows; products: {product_total:,} rows")
    print(f"Product-ID match rate: {match_percentage:.2f}%")
    print(
        f"Ratings outside 1-5: {out_of_range_ratings:,}; "
        f"non-integer ratings: {non_integer_ratings:,}; blank review text: {blank_text:,}"
    )
    print(f"Repeated core review rows (candidate): {repeated_core:,}")
    print(f"Saved detailed quality report: {OUTPUT_FILE}")
    print("Note: repeated core rows are candidates for review, not automatic deletions.")


if __name__ == "__main__":
    main()