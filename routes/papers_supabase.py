from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase

router = APIRouter(prefix="/papers-sb", tags=["Papers (Supabase)"])


@router.get("")
@router.get("/")  # support both forms
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

        # ✅ Full-text search
        if q:
            query = query.ilike("title", f"%{q}%")

        # ✅ Topic → keyword mapping
        topic_map = {
            # UI sends: ?topic=treat
            "treat": ["treat", "therapy", "trial", "drug", "intervention"],

            # UI sends: ?topic=neuro
            "neuro": ["neuro", "brain", "cogn", "nervous"],

            # UI sends: ?topic=immun
            "immun": ["immune", "inflamm", "cytokine", "t cell", "antibody"],

            # UI sends: ?topic=covid
            "covid": ["covid", "post-viral", "long covid", "sars"],
        }

        if topic in topic_map:
            terms = topic_map[topic]

            # ✅ Build OR filter (Supabase syntax)
            or_filters = []
            for term in terms:
                or_filters.append(f"title.ilike.%{term}%")
                or_filters.append(f"abstract.ilike.%{term}%")

            query = query.or_(",".join(or_filters))

        # ✅ Year filter
        if year:
            query = query.eq("year", year)

        # ✅ Cluster filter (not used on this page, but keep for compatibility)
        if cluster is not None:
            query = query.eq("cluster", cluster)

        # (Sort still accepted but not implemented here)

        result = query.execute()
        data = result.data or []

        # ✅ Stop infinite scroll when empty
        return {
            "data": data,
            "page": page,
            "count": len(data),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching papers: {str(e)}")
