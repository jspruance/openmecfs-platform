# routes/papers_recent.py
from fastapi import APIRouter
from utils.db import supabase

router = APIRouter(prefix="/papers/summaries", tags=["papers"])


@router.get("/recent")
def recent_summaries(limit: int = 10):
    """
    Return most recent AI mechanistic paper summaries
    for Research Lab live feed.
    """
    res = (
        supabase.table("paper_summaries")
        .select("paper_pmid, one_sentence, confidence, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return res.data or []
