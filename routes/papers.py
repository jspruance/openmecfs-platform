# routes/papers.py
from fastapi import APIRouter, HTTPException, Query
from utils.loader import load_data
from pathlib import Path
from datetime import datetime
from typing import List

router = APIRouter(prefix="/papers", tags=["papers"])
papers = load_data()


# 🧩 1️⃣ List Papers (with sort, filters, pagination, fields)
@router.get("/")
def list_papers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("pmid", description="Sort by pmid, title, or author"),
    order: str = Query("asc", description="asc or desc"),
    author: str | None = Query(None, description="Filter by author substring"),
    year: int | None = Query(
        None, description="Filter by publication year (if available)"),
    keyword: str | None = Query(
        None, description="Filter by keyword in title, abstract, or summaries"),
    fields: str | None = Query(
        None, description="Comma-separated list of fields to return, e.g. pmid,title,patient_summary"),
):
    """Return paginated, sortable, and filterable list of papers."""
    if not papers:
        return {"message": "No summarized papers available yet. Please upload a dataset."}

    filtered = papers

    # ✅ Author filter
    if author:
        filtered = [
            p for p in filtered
            if any(author.lower() in a.lower() for a in p.get("authors", []))
        ]

    # ✅ Year filter (optional if 'year' present)
    if year:
        filtered = [p for p in filtered if p.get("year") == year]

    # ✅ Keyword filter
    if keyword:
        keyword_lower = keyword.lower()
        filtered = [
            p for p in filtered
            if keyword_lower in p.get("title", "").lower()
            or keyword_lower in p.get("abstract", "").lower()
            or keyword_lower in p.get("technical_summary", "").lower()
            or keyword_lower in p.get("patient_summary", "").lower()
        ]

    # ✅ Sorting
    sort_key = sort.lower()
    valid_sorts = {"pmid", "title", "authors"}
    if sort_key not in valid_sorts:
        sort_key = "pmid"

    sorted_papers = sorted(
        filtered,
        key=lambda p: (
            p.get(sort_key)
            if sort_key != "authors"
            else (", ".join(p.get("authors", [])) if p.get("authors") else "")
        ),
        reverse=(order == "desc"),
    )

    # ✅ Pagination
    start = (page - 1) * limit
    end = start + limit
    results = sorted_papers[start:end]

    # ✅ Field selection
    if fields:
        requested_fields = [f.strip() for f in fields.split(",") if f.strip()]
        results = [
            {k: v for k, v in p.items() if k in requested_fields}
            for p in results
        ]

    return {
        "page": page,
        "limit": limit,
        "total": len(filtered),
        "sort": sort_key,
        "order": order,
        "filters": {"author": author, "year": year, "keyword": keyword},
        "results": results,
    }


# 🧠 2️⃣ Metadata Endpoint
@router.get("/meta")
def get_metadata():
    """Return dataset and model metadata."""
    meta = {
        "project": "Open ME/CFS",
        "dataset_found": bool(papers),
        "total_papers": len(papers),
        "latest_summary_date": None,
        "technical_model": None,
        "patient_model": None,
    }

    if not papers:
        return meta

    # Extract metadata from first paper
    first_meta = papers[0].get("metadata", {})
    meta["technical_model"] = first_meta.get("technical_summary_model")
    meta["patient_model"] = first_meta.get("patient_summary_model")
    meta["latest_summary_date"] = first_meta.get("summarized_at")

    # Determine latest file
    data_path = Path(__file__).resolve().parents[1] / "data"
    files = sorted(data_path.glob(
        "mecfs_papers_summarized_*.json"), reverse=True)
    if files:
        latest_file = files[0]
        meta["dataset_file"] = latest_file.name
        meta["dataset_last_modified"] = datetime.fromtimestamp(
            latest_file.stat().st_mtime
        ).isoformat()

    return meta


# 🔍 3️⃣ Search Endpoint
@router.get("/search/")
def search_papers(q: str = Query(..., description="Search term")):
    """Full-text search across title, abstract, and summaries."""
    if not papers:
        return {"message": "No summarized papers available yet."}

    results = [
        p for p in papers
        if q.lower() in p.get("title", "").lower()
        or q.lower() in p.get("abstract", "").lower()
        or q.lower() in p.get("technical_summary", "").lower()
        or q.lower() in p.get("patient_summary", "").lower()
    ]
    return {"query": q, "count": len(results), "results": results}


# 💬 4️⃣ Suggest (Autocomplete) Endpoint
@router.get("/suggest")
def suggest_terms(
    q: str = Query(..., description="Partial search term (min 2 chars)"),
    limit: int = Query(10, ge=1, le=50),
):
    """Return lightweight autocomplete suggestions (titles + authors)."""
    if not papers:
        return {"message": "No summarized papers available yet."}

    query = q.strip().lower()
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="Query too short")

    suggestions = set()

    for p in papers:
        title = p.get("title", "")
        authors = p.get("authors", [])
        if query in title.lower():
            suggestions.add(title)
        for a in authors:
            if query in a.lower():
                suggestions.add(a)

        # Optional: also match patient summaries
        summary = p.get("patient_summary", "")
        if query in summary.lower():
            snippet = " ".join(summary.split()[:10]) + "..."
            suggestions.add(snippet)

        if len(suggestions) >= limit:
            break

    return {
        "query": q,
        "count": len(suggestions),
        "suggestions": list(suggestions)[:limit],
    }


# 📄 5️⃣ Get Single Paper by PMID
@router.get("/{pmid}")
def get_paper(pmid: str):
    """Return details for a specific paper."""
    if not papers:
        raise HTTPException(status_code=404, detail="No papers loaded.")

    for paper in papers:
        if paper.get("pmid") == pmid:
            return paper

    raise HTTPException(status_code=404, detail="Paper not found")
