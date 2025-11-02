# routes/papers_sync.py

from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.europepmc import fetch_pmc_data

router = APIRouter(prefix="/papers", tags=["Papers"])


@router.post("/sync/{pmid}")
async def sync_paper(pmid: str):
    # 1️⃣ See if the paper already exists in Supabase
    existing = supabase.table("papers").select(
        "*").eq("pmid", pmid).maybe_single().execute()
    if existing.data:
        return existing.data

    # 2️⃣ Fetch metadata from Europe PMC
    data = await fetch_pmc_data(pmid)
    if not data:
        raise HTTPException(
            status_code=404, detail=f"PMID {pmid} not found on EuropePMC")

    # Defensive defaults
    title = data.get("title") or ""
    abstract = data.get("abstract") or ""
    journal = data.get("journal") or ""
    year = data.get("year") or None
    authors = data.get("authors") or ""

    # 3️⃣ Insert into Supabase papers table
    payload = {
        "pmid": pmid,
        "title": title.strip(),
        "abstract": abstract.strip(),
        "journal": journal.strip(),
        "year": year,
        "authors": authors if isinstance(authors, list) else [authors],
    }

    res = supabase.table("papers").insert(payload).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to insert paper")

    return res.data[0]
