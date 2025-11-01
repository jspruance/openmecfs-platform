from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase

router = APIRouter(prefix="/papers-sb", tags=["Papers (Supabase)"])


@router.get("/")
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

        if q:
            query = query.ilike("title", f"%{q}%")

        topic_map = {
            "treat": ["treat", "therapy", "trial", "drug", "intervention"],
            "neuro": ["neuro", "brain", "cogn", "nervous"],
            "immun": ["immune", "inflamm", "cytokine", "t cell", "antibody"],
            "covid": ["covid", "post-viral", "long covid", "sars"],
        }

        if topic in topic_map:
            terms = topic_map[topic]
            or_filters = []
            for term in terms:
                or_filters.append(f"title.ilike.%{term}%")
                or_filters.append(f"abstract.ilike.%{term}%")

            or_query = ",".join(or_filters)
            query = query.or_(or_query)

        if year:
            query = query.eq("year", year)

        if cluster is not None:
            query = query.eq("cluster", cluster)

        result = query.execute()
        data = result.data or []

        return {
            "data": data,
            "page": page,
            "count": len(data),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching papers: {str(e)}")
