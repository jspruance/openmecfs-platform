# openmecfs-platform/routes/papers_supabase.py
# serves the /research/subtypes page
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase

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
    cluster_label: Optional[int] = None,  # ✅ support alt name
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

        # ✅ Filter by cluster
        # Note: papers table uses 'cluster' column to match subtype_clusters.cluster_id
        cluster_id = cluster if cluster is not None else cluster_label
        if cluster_id is not None:
            # Filter papers by cluster value
            query = query.eq("cluster", cluster_id)

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
            status_code=500, detail=f"Error fetching papers: {str(e)}")
