# routes/papers_supabase.py
# cmt
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

        # ✅ Filter by cluster
        if cluster is not None:
            query = query.eq("cluster", cluster)

        # ✅ Filter by year
        if year is not None:
            query = query.eq("year", year)

        # ✅ Filter by query string
        if q:
            query = query.ilike("title", f"%{q}%")

        result = query.execute()
        return result.data or []

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching papers: {str(e)}"
        )


# ✅ UI-compatible route: /papers-sb?sort=year&limit=10&page=1
@router.get("/list")
def get_papers_ui(
    sort: Optional[str] = Query(
        "year", description="Sort field (ignored for now)"),
    limit: int = Query(10, ge=1, le=200),
    page: int = Query(1, ge=1)
):
    """
    UI endpoint to fetch ME/CFS papers using page, limit, sort
    """
    offset = (page - 1) * limit

    try:
        query = supabase.table("papers").select(
            "*").range(offset, offset + limit - 1)

        # NOTE: Sort not implemented yet — UI just needs param accepted.
        # Future: query.order(sort)

        result = query.execute()
        return result.data or []

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching papers: {str(e)}"
        )
