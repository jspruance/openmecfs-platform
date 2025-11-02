# routes/papers_sync.py

from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.europepmc import fetch_pmc_data

router = APIRouter(prefix="/papers", tags=["Papers"])


@router.post("/sync/{pmid}")
def sync_paper(pmid: str):
    """
    Sync a paper from EuropePMC into Supabase `papers` table.
    If it already exists, return the existing row.
    """

    # 1️⃣ Check if paper already exists
    existing = (
        supabase.table("papers")
        .select("*")
        .eq("pmid", pmid)
        .maybe_single()
        .execute()
    )

    if existing.data:
        return existing.data

    # 2️⃣ Fetch from EuropePMC
    data = fetch_pmc_data(pmid)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"PMID {pmid} not found on EuropePMC"
        )

    # Defensive defaults
    title = (data.get("title") or "").strip()
    abstract = (data.get("abstract") or "").strip()
    journal = (data.get("journal") or "").strip()
    year = data.get("year") or None
    authors = data.get("authors") or []

    # Ensure authors is always a list
    if not isinstance(authors, list):
        authors = [authors]

    # 3️⃣ Insert into Supabase
    payload = {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "journal": journal,
        "year": year,
        "authors": authors,
    }

    res = supabase.table("papers").insert(payload).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to insert paper")

    return res.data[0]
