# routes/papers.py
from fastapi import APIRouter, HTTPException, Query
from utils.db import (
    get_papers,
    get_paper_by_pmid,
    search_papers,
    get_metadata,
    supabase,
)
from openai import OpenAI
import os

router = APIRouter(prefix="/papers", tags=["papers"])

# ------------------------------------------------------------
#  📘 1️⃣ List & Metadata Endpoints
# ------------------------------------------------------------


@router.get("/")
def list_papers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("pmid"),
    order: str = Query("asc"),
):
    """Return paginated list of papers"""
    offset = (page - 1) * limit
    results = get_papers(limit=limit, offset=offset, sort=sort, order=order)
    return {"page": page, "limit": limit, "count": len(results), "results": results}


@router.get("/meta")
def meta():
    """Return most recent dataset metadata"""
    meta = get_metadata()
    if not meta:
        return {"message": "No dataset metadata found. Try re-importing."}
    return meta


# ------------------------------------------------------------
#  🔍 2️⃣ Search Endpoints
# ------------------------------------------------------------

@router.get("/search")
def search(
    q: str | None = None,
    limit: int = 10,
    author: str | None = None,
    year: int | None = None,
):
    """Full-text search with optional author/year filters"""
    results = search_papers(q, limit, author, year)
    if not results:
        return {"message": f"No results found for '{q or 'query'}'."}

    return {
        "query": q,
        "filters": {"author": author, "year": year},
        "count": len(results),
        "results": results,
    }


@router.get("/suggest")
def suggest(q: str, limit: int = 5):
    """Autocomplete suggestions (titles only)"""
    results = search_papers(q, limit)
    suggestions = [{"pmid": r["pmid"], "title": r["title"]} for r in results]
    return {"query": q, "suggestions": suggestions}


# ------------------------------------------------------------
#  🧠 3️⃣ Semantic Search (OpenAI + pgvector)
# ------------------------------------------------------------

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_MODEL = "text-embedding-3-small"


@router.get("/semantic")
def semantic_search(
    q: str = Query(..., description="Semantic search query"),
    limit: int = Query(5, ge=1, le=20),
):
    """Semantic similarity search using OpenAI embeddings + Supabase RPC"""
    try:
        # Create query embedding
        embedding = _client.embeddings.create(
            input=q, model=_MODEL
        ).data[0].embedding

        # Query pgvector via RPC
        res = supabase.rpc(
            "match_papers", {
                "query_embedding": embedding, "match_count": limit}
        ).execute()

        return {
            "query": q,
            "count": len(res.data or []),
            "results": res.data or [],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------
#  📄 4️⃣ Single Paper (keep LAST to avoid route collisions)
# ------------------------------------------------------------

@router.get("/{pmid}")
def get_paper(pmid: str):
    """Fetch single paper by PMID"""
    result = get_paper_by_pmid(pmid)
    if not result:
        raise HTTPException(status_code=404, detail="Paper not found")
    return result
