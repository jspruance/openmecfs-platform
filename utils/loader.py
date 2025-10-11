# utils/loader.py
import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data"


def load_data(filename: str | None = None):
    """Load summarized ME/CFS papers from JSON.
    If no dataset is found, return an empty list and log a warning."""
    try:
        if not filename:
            files = sorted(DATA_PATH.glob(
                "mecfs_papers_summarized_*.json"), reverse=True)
            if not files:
                print(
                    "⚠️  No summarized dataset found. The API will start with empty data.")
                return []

            filename = files[0]

        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both array and wrapped formats
        if isinstance(data, dict) and "papers" in data:
            return data["papers"]
        return data

    except Exception as e:
        print(f"⚠️  Error loading dataset: {e}")
        return []
