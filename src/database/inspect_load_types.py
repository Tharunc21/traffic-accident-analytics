
"""
Inspect cleaned CSV values against PostgreSQL column types.
This script only reads data and schema; it does not modify the database.
Run from the project root:
    python .\src\database\inspect_load_types.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = PROJECT_ROOT / "data" / "staging"

DATASETS = [
    ("collisions_cleaned.csv", "cleaned.collisions"),
    ("vehicles_cleaned.csv", "cleaned.vehicles"),
    ("casualties_cleaned.csv", "cleaned.casualties"),
]

INTEGER_TYPES = {"smallint", "integer", "bigint"}
NUMERIC_TYPES = {"numeric", "real", "double precision", "decimal"}

def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for filename, table_name in DATASETS:
                path = STAGING_DIR / filename
                print(f"\n=== {table_name} ({filename}) ===")
                cur.execute(
                    """
                    SELECT column_name, data_type, udt_name
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    tuple(table_name.split(".")),
                )
                schema = cur.fetchall()
                if not schema:
                    print("ERROR: table not found")
                    continue

                with path.open("r", encoding="utf-8-sig", newline="") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames or []
                    db_names = [r[0] for r in schema]
                    if set(headers) != set(db_names):
                        print("HEADER MISMATCH:")
                        print("  CSV-only:", sorted(set(headers) - set(db_names)))
                        print("  DB-only: ", sorted(set(db_names) - set(headers)))

                    # Inspect distinct values for DB numeric columns.
                    numeric_columns = [
                        (name, dtype) for name, dtype, _ in schema
                        if dtype in INTEGER_TYPES or dtype in NUMERIC_TYPES
                    ]
                    examples = {name: set() for name, _ in numeric_columns}
                    non_numeric = {name: set() for name, _ in numeric_columns}
                    row_count = 0
                    for row in reader:
                        row_count += 1
                        for name, dtype in numeric_columns:
                            value = (row.get(name) or "").strip()
                            if not value:
                                continue
                            examples[name].add(value)
                            try:
                                if dtype in INTEGER_TYPES:
                                    int(value)
                                else:
                                    float(value)
                            except ValueError:
                                if len(non_numeric[name]) < 8:
                                    non_numeric[name].add(value)
                    print(f"CSV rows: {row_count:,}")
                    if not any(non_numeric.values()):
                        print("No non-numeric values found in numeric DB columns.")
                    for name, vals in non_numeric.items():
                        if vals:
                            print(f"  {name}: text values incompatible with numeric type: {sorted(vals)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

