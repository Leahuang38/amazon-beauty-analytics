"""Inspect the Amazon All_Beauty review and product data.

Concepts used: variables, lists, loops, dictionaries, conditionals, exceptions,
file paths, and DuckDB SQL. Run from the project root:
    python scripts/01_inspect_data.py
"""

from pathlib import Path

import duckdb


# Build paths relative to this file so the script works from any terminal folder.
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
FILES = {
    "reviews": RAW_DIR / "All_Beauty.jsonl.gz",
    "products": RAW_DIR / "meta_All_Beauty.jsonl.gz",
}

missing = [name for name, path in FILES.items() if not path.exists()]

if missing:
    print("Missing files:", ", ".join(missing))
    print("Download links and instructions are in README.md.")
else:
    connection = duckdb.connect(database=":memory:")
    try:
        for label, path in FILES.items():
            # Convert the path to SQL-safe text before inserting it into a query.
            sql_path = str(path).replace("'", "''")
            row_count = connection.execute(
                f"SELECT COUNT(*) FROM read_json_auto('{sql_path}')"
            ).fetchone()[0]
            columns = connection.execute(
                f"DESCRIBE SELECT * FROM read_json_auto('{sql_path}')"
            ).fetchall()

            print(f"\n{label.title()} records: {row_count:,}")
            print("Fields:", [column[0] for column in columns])

            sample = connection.execute(
                f"SELECT * FROM read_json_auto('{sql_path}') LIMIT 2"
            ).df()
            print("Example rows:")
            print(sample.to_string(index=False, max_colwidth=100))
    except (OSError, duckdb.Error) as error:
        # Show a readable message if a download is incomplete or a file is invalid.
        print("Could not read the dataset:", error)
    finally:
        connection.close()
