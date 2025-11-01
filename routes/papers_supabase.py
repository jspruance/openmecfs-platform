# routes/papers_supabase.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase

router = APIRouter(prefix="/papers-sb", tags=["Papers (Supabase)"])

# ✅ Allow both `/papers-sb` and `/papers-sb/`


@router.get("")
@router.get("/")
def get_papers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    sort: Optional[str] = Query("year", description="Sort field"),
    cluster: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
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

        result = query.execute()
        return result.data or []

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching papers: {str(e)}")
