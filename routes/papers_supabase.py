from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase

router = APIRouter(prefix="/papers-sb", tags=["Papers (Supabase)"])


@router.get("")
def get_papers(
    sort: Optional[str] = Query("year"),
    limit: int = Query(10, ge=1, le=200),
    page: int = Query(1, ge=1),
    topic: Optional[str] = None,
    q: Optional[str] = None,
    year: Optional[int] = None,
    cluster: Optional[int] = None,
):
    try:
        offset = (page - 1) * limit

        query = (
            supabase
            .table("papers")
            .select("*")
            .range(offset, offset + limit - 1)
        )

        # Full-text search
        if q:
            query = query.ilike("title", f"%{q}%")

        # ✅ Topic filter — search in title & abstract
        if topic:
            query = query.or_(
                f"title.ilike.%{topic}%,abstract.ilike.%{topic}%"
            )

        # ✅ Year filter
        if year:
            query = query.eq("year", year)

        # ✅ Cluster filter
        if cluster is not None:
            query = query.eq("cluster", cluster)

        # (Sort param ignored but accepted — no crash)

        result = query.execute()
        data = result.data or []

        # ✅ Stop infinite scroll when no results
        return {
            "data": data,
            "page": page,
            "count": len(data),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
