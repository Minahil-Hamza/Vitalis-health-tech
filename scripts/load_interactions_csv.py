"""Load the founder-authored drug interaction CSV directly into the database.

Run after applying migrations: python scripts/load_interactions_csv.py
Or point it at a different file: python scripts/load_interactions_csv.py path/to/file.csv

Expects the same columns as the admin CSV import endpoint:
drug_a,drug_b,severity,description,recommendation
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.services.drug_interactions_import import import_interactions_from_csv_text

DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent / "drug_interactions_seed.csv"


def load(csv_path: Path):
    """Read csv_path and insert its rows into the drug_interactions table."""
    if not csv_path.exists():
        print(f"No file at {csv_path}. Place your CSV there (or pass a path as an argument) and try again.")
        sys.exit(1)

    csv_text = csv_path.read_text(encoding="utf-8")
    db = SessionLocal()
    try:
        result = import_interactions_from_csv_text(csv_text, db)
    finally:
        db.close()

    print(f"Imported {result['imported']} interaction(s) from {csv_path.name}.")
    if result["errors"]:
        print(f"\n{len(result['errors'])} row(s) skipped:")
        for error in result["errors"]:
            print(f"  {error}")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV_PATH
    load(path)
