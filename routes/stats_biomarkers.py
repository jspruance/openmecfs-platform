# routes/stats_biomarkers.py
from fastapi import APIRouter
from utils.db import supabase
from collections import Counter

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/biomarker_counts")
def biomarker_counts(limit: int = 20):
    """
    Returns most frequently appearing biomarkers from structured AI evidence.
    """
    res = (
        supabase.table("paper_summaries")
        .select("biomarkers")
        .not_.is_("biomarkers", None)
        .execute()
    )

    all_biomarkers = []
    for row in res.data or []:
        for b in (row.get("biomarkers") or []):
            b = b.strip()
            if b:
                all_biomarkers.append(b)

    counts = Counter(all_biomarkers).most_common(limit)

    return [{"biomarker": b, "count": c} for b, c in counts]
