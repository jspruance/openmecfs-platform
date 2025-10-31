# routes/papers_supabase.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase

router = APIRouter(prefix="/papers-sb", tags=["Papers (Supabase)"])


@router.get("/")
def get_papers(
    cluster: Optional[int] = Query(
        None, alias="cluster", description="Filter by cluster number"),
    year: Optional[int] = Query(
        None, description="Filter by publication year"),
    q: Optional[str] = Query(None, description="Search by keyword or title"),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Fetch ME/CFS papers from Supabase with optional filters.
    """
    try:
        query = supabase.table("papers").select(
            "*").range(offset, offset + limit - 1)

        # ✅ Correct column name in Supabase
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
            status_code=500, detail=f"Error fetching papers: {str(e)}"
        )
