# openmecfs-platform/routes/papers_supabase.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase

# No prefix here — main.py applies it
router = APIRouter(tags=["Papers (Supabase)"])


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
            query = query.or_(f"title.ilike.%{q}%,abstract.ilike.%{q}%")

        topic_map = {
            "treat": ["treat", "therapy", "trial", "drug", "intervention"],
            "neuro": ["neuro", "brain", "cogn", "nervous"],
            "immun": ["immune", "inflamm", "cytokine", "t cell", "antibody"],
            "long covid": ["long covid", "covid", "post-viral", "sars"],
        }

        if topic:
            topic = topic.lower().replace("-", " ")
            if topic in topic_map:
                filters = []
                for term in topic_map[topic]:
                    filters += [f"title.ilike.%{term}%",
                                f"abstract.ilike.%{term}%"]
                query = query.or_(",".join(filters))

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
            "has_more": len(data) == limit,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching papers: {str(e)}"
        )
