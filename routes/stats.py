# routes/stats.py
from fastapi import APIRouter
from utils.db import get_stats
from functools import lru_cache
from datetime import datetime

router = APIRouter(prefix="/stats", tags=["stats"])


# ------------------------------------------------------------
# 📊 Dataset Statistics Endpoints
# ------------------------------------------------------------

@router.get("/")
def stats():
    """Return live statistics for ME/CFS dataset (fetched fresh from Supabase)"""
    data = get_stats()
    return {
        **data,
        "source": "live",
        "generated_at": datetime.utcnow().isoformat(),
    }


@lru_cache(maxsize=1)
def _cached_stats_internal():
    """Internal cached helper — stores results in memory"""
    return get_stats()


@router.get("/cached")
def cached_stats():
    """Return cached statistics for faster UI rendering"""
    data = _cached_stats_internal()
    return {
        **data,
        "source": "cached",
        "cached_at": datetime.utcnow().isoformat(),
    }
