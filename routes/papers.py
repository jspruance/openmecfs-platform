# routes/papers.py
from fastapi import APIRouter, HTTPException, Query
from utils.db import get_papers, get_paper_by_pmid, search_papers, get_metadata

router = APIRouter(prefix="/papers", tags=["papers"])

# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------


@router.get("/")
def list_papers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("pmid"),
    order: str = Query("asc")
):
    offset = (page - 1) * limit
    results = get_papers(limit=limit, offset=offset, sort=sort, order=order)
    return {"page": page, "limit": limit, "count": len(results), "results": results}


@router.get("/search")
def search(
    q: str | None = None,
    limit: int = 10,
    author: str | None = None,
    year: int | None = None,
):
    """Smart full-text search with optional filters"""
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
    """Autocomplete: return top-matching titles only"""
    results = search_papers(q, limit)
    suggestions = [{"pmid": r["pmid"], "title": r["title"]} for r in results]
    return {"query": q, "suggestions": suggestions}


@router.get("/meta")
def meta():
    meta = get_metadata()
    if not meta:
        return {"message": "No dataset metadata found. Try re-importing."}
    return meta


@router.get("/{pmid}")
def get_paper(pmid: str):
    result = get_paper_by_pmid(pmid)
    if not result:
        raise HTTPException(status_code=404, detail="Paper not found")
    return result
