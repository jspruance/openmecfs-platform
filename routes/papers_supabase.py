# routes/papers_supabase.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase

router = APIRouter(prefix="/papers-sb", tags=["Papers (Supabase)"])

# ✅ UI & API both hit this endpoint


@router.get("")
def get_papers(
    sort: Optional[str] = Query("year", description="Sort field"),
    limit: int = Query(10, ge=1, le=200),
    page: int = Query(1, ge=1),
    cluster: Optional[int] = None,
    year: Optional[int] = None,
    q: Optional[str] = None,
):
    try:
        offset = (page - 1) * limit

        query = (
            supabase
            .table("papers")
            .select("*")
            .range(offset, offset + limit - 1)
        )

        if cluster is not None:
            query = query.eq("cluster", cluster)

        if year is not None:
            query = query.eq("year", year)

        if q:
            query = query.ilike("title", f"%{q}%")

        # ✅ allow the sort param even if we ignore for now
        # future: query.order(sort)

        result = query.execute()
        return result.data or []

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
