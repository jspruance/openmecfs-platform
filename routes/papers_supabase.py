# openmecfs-platform/routes/papers_supabase.py

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

        # ✅ full text search
        if q:
            query = query.or_(
                f"title.ilike.%{q}%,abstract.ilike.%{q}%"
            )

        # ✅ Expanded topic keywords to match UI buttons
        topic_map = {
            "treat": ["treat", "therapy", "trial", "drug", "intervention"],
            "neurology": ["neuro", "brain", "cogn", "nervous"],
            "immunology": ["immune", "inflamm", "cytokine", "t cell", "antibody"],
            "long covid": ["long covid", "covid", "post-viral", "sars"],
        }

        # Normalize incoming topic (lowercase)
        if topic:
            topic = topic.lower().replace("-", " ")

        # ✅ topic filter (title + abstract)
        if topic in topic_map:
            terms = topic_map[topic]
            or_filters = []
            for term in terms:
                or_filters.append(f"title.ilike.%{term}%")
                or_filters.append(f"abstract.ilike.%{term}%")

            query = query.or_(",".join(or_filters))

        # ✅ year filter
        if year:
            query = query.eq("year", year)

        # ✅ cluster filter
        if cluster is not None:
            query = query.eq("cluster", cluster)

        result = query.execute()
        data = result.data or []

        # ✅ stop infinite scroll — no more pages if empty
        return {
            "data": data,
            "page": page,
            "has_more": len(data) == limit,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching papers: {str(e_
