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
    """Load ME/CFS papers from JSON and normalize key fields.

    Priority:
      1. mecfs_papers_summarized_*.json (latest summarized dataset)
      2. raw_papers.json (fallback if no summarized file)

    Adds:
      - `year`: inferred publication year if available
      - `imported_at`: timestamp of load
    """
    try:
        if filename:
            path = Path(filename)
        else:
            # Look for latest summarized dataset first
            summarized_files = sorted(DATA_PATH.glob(
                "mecfs_papers_summarized_*.json"), reverse=True)
            if summarized_files:
                path = summarized_files[0]
            else:
                # Fallback to raw dataset
                path = DATA_PATH / "raw_papers.json"

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both array and wrapped formats
        papers = data["papers"] if isinstance(
            data, dict) and "papers" in data else data

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

        print(
            f"✅ Loaded {len(normalized)} papers from {path.name} with normalized year field.")
        return normalized

    except Exception as e:
        print(f"⚠️  Error loading dataset: {e}")
        return []
