import json
from pathlib import Path
from datetime import datetime

DATA_PATH = Path(__file__).resolve().parents[1] / "data"


def infer_year(paper: dict) -> int | None:
    """Try to infer publication year from multiple possible keys."""
    for key in ("pubdate", "publication_date", "publicationYear", "year", "date", "published"):
        if key in paper and paper[key]:
            try:
                # Handle both YYYY-MM-DD and YYYY formats
                return int(str(paper[key])[:4])
            except Exception:
                pass

    # Try nested metadata object
    metadata = paper.get("metadata") or {}
    for key in ("year", "publication_date", "date"):
        if key in metadata and metadata[key]:
            try:
                return int(str(metadata[key])[:4])
            except Exception:
                pass

    return None


def load_data(filename: str | None = None):
    """Load summarized ME/CFS papers from JSON and normalize key fields.

    Adds:
      - `year`: inferred publication year if available
      - `imported_at`: timestamp of load
    """
    try:
        if not filename:
            files = sorted(
                DATA_PATH.glob("mecfs_papers_summarized_*.json"), reverse=True
            )
            if not files:
                print(
                    "⚠️  No summarized dataset found. The API will start with empty data."
                )
                return []

            filename = files[0]

        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both array and wrapped formats
        if isinstance(data, dict) and "papers" in data:
            papers = data["papers"]
        else:
            papers = data

        normalized = []
        for p in papers:
            year = infer_year(p)
            normalized.append(
                {
                    **p,
                    "year": year,
                    "imported_at": datetime.utcnow().isoformat(),
                }
            )

        print(f"✅ Loaded {len(normalized)} papers with normalized year field.")
        return normalized

    except Exception as e:
        print(f"⚠️  Error loading dataset: {e}")
        return []
