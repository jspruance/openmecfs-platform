# openmecfs-platform/routes/papers_supabase.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.db import supabase
from utils.europepmc import fetch_pmc_data
import datetime

router = APIRouter(tags=["Papers (Supabase)"])


# ============================================================
# GET /papers → support subtypes + research explorer UI
# ============================================================
@router.get("/")
def get_papers(
    sort: Optional[str] = Query("year"),
    limit: int = Query(10, ge=1, le=200),
    page: int = Query(1, ge=1),
    topic: Optional[str] = None,
    q: Optional[str] = None,
    year: Optional[int] = None,
    cluster: Optional[int] = None,
    cluster_label: Optional[int] = None,
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

        cluster_id = cluster if cluster is not None else cluster_label
        if cluster_id is not None:
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
            status_code=500, detail=f"Error fetching papers: {str(e)}"
        )


# ============================================================
# POST /papers/sync/{pmid}
# Sync a paper into Supabase & return DB record (with UUID)
# ============================================================
@router.post("/sync/{pmid}")
def sync_paper(pmid: str):
    # 1️⃣ Fetch from Europe PMC
    metadata = fetch_pmc_data(pmid)
    if not metadata:
        raise HTTPException(
            status_code=404, detail=f"PMID {pmid} not found on EuropePMC"
        )

    # 2️⃣ Build DB object
    row = {
        "pmid": pmid,
        "title": metadata.get("title"),
        "abstract": metadata.get("abstract"),
        "authors": metadata.get("authors") or [],
        "authors_text": metadata.get("authors_text") or None,  # ✅ new field
        "journal": metadata.get("journal"),
        "year": int(metadata["year"]) if metadata.get("year") else None,
        "fetched_at": datetime.datetime.utcnow().isoformat(),
    }

    # 3️⃣ Upsert into Supabase
    supabase.table("papers").upsert(row).execute()

    # 4️⃣ Read back row to return Supabase UUID
    db_paper = (
        supabase.table("papers")
        .select("*")
        .eq("pmid", pmid)
        .maybe_single()
        .execute()
    )

    if not db_paper or not db_paper.data:
        raise HTTPException(
            status_code=500, detail="Failed to read back paper after upsert"
        )

    return db_paper.data
