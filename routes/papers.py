from fastapi import APIRouter, HTTPException, Query
from utils.loader import load_data
from pathlib import Path
import json
from datetime import datetime

router = APIRouter(prefix="/papers", tags=["papers"])
papers = load_data()


@router.get("/")
def list_papers(skip: int = 0, limit: int = 10):
    """Return paginated list of papers"""
    if not papers:
        return {"message": "No summarized papers available yet. Please upload a dataset."}
    return {"total": len(papers), "results": papers[skip: skip + limit]}

# ✅ Move this ABOVE /{pmid}


@router.get("/meta")
def get_metadata():
    """Return dataset and model metadata"""
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

    first_meta = papers[0].get("metadata", {})
    meta["technical_model"] = first_meta.get("technical_summary_model")
    meta["patient_model"] = first_meta.get("patient_summary_model")
    meta["latest_summary_date"] = first_meta.get("summarized_at")

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


@router.get("/search/")
def search_papers(q: str = Query(..., description="Search term")):
    """Search across title, abstract, and summaries"""
    results = [
        p for p in papers
        if q.lower() in p.get("title", "").lower()
        or q.lower() in p.get("abstract", "").lower()
        or q.lower() in p.get("technical_summary", "").lower()
        or q.lower() in p.get("patient_summary", "").lower()
    ]
    return {"query": q, "count": len(results), "results": results}


@router.get("/{pmid}")
def get_paper(pmid: str):
    """Return details for a specific paper"""
    for paper in papers:
        if paper.get("pmid") == pmid:
            return paper
    raise HTTPException(status_code=404, detail="Paper not found")
