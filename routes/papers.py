from fastapi import APIRouter, HTTPException, Query
from utils.loader import load_data
from typing import List

router = APIRouter(prefix="/papers", tags=["papers"])

# 🧩 Load dataset once at startup
papers = load_data()


# 🧠 List Papers (with filters, pagination, sorting)
@router.get("/")
def list_papers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("pmid", description="Sort by pmid, title, or author"),
    order: str = Query("asc", description="asc or desc"),
    author: str | None = Query(None, description="Filter by author substring"),
    year: int | None = Query(None, description="Filter by publication year"),
):
    # Defensive check
    if not papers:
        return []

    results = papers

    # Optional filter by author substring
    if author:
        results = [
            p for p in results if any(author.lower() in a.lower() for a in p.get("authors", []))
        ]

    # Optional filter by year
    if year:
        results = [p for p in results if p.get("year") == year]

    # Sorting
    reverse = order.lower() == "desc"
    try:
        results = sorted(results, key=lambda x: str(
            x.get(sort, "")).lower(), reverse=reverse)
    except KeyError:
        pass

    # Pagination
    start = (page - 1) * limit
    end = start + limit
    return results[start:end]


# 🔍 Search Endpoint
@router.get("/search")
def search_papers(q: str = Query(..., description="Full-text search")):
    q_lower = q.lower()
    matched = [
        p
        for p in papers
        if q_lower in p.get("title", "").lower()
        or q_lower in p.get("abstract", "").lower()
        or q_lower in " ".join(p.get("authors", [])).lower()
    ]
    return matched[:20]


# 📄 Single Paper by PMID
@router.get("/{pmid}")
def get_paper(pmid: str):
    """Return full record for one paper, including summaries and abstract."""
    if not papers:
        raise HTTPException(status_code=500, detail="No papers loaded")

    for paper in papers:
        if str(paper.get("pmid")) == str(pmid):
            return paper

    raise HTTPException(status_code=404, detail=f"Paper {pmid} not found")
