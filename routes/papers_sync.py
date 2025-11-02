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

    print(f"[SYNC] Checking Supabase for PMID {pmid}")

    # 1️⃣ Check if paper already exists (safe handling)
    try:
        existing = (
            supabase.table("papers")
            .select("*")
            .eq("pmid", pmid)
            .maybe_single()
            .execute()
        )
    except Exception as e:
        print(f"[SYNC ERROR] Supabase query failed: {e}")
        existing = None

    # ✅ Prevent NoneType crash
    if existing and getattr(existing, "data", None):
        print(f"[SYNC] Found cached paper for PMID {pmid}")
        return existing.data

    print(f"[SYNC] Fetching from EuropePMC for PMID {pmid}")
    data = fetch_pmc_data(pmid)

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"PMID {pmid} not found on EuropePMC"
        )

    # Normalize fields
    title = (data.get("title") or "").strip()
    abstract = (data.get("abstract") or "").strip()
    journal = (data.get("journal") or "").strip()
    year = data.get("year") or None
    authors = data.get("authors") or []

    if not isinstance(authors, list):
        authors = [authors]

    payload = {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "journal": journal,
        "year": year,
        "authors": authors,
    }

    print(f"[SYNC] Inserting into Supabase... {payload}")

    # 3️⃣ Insert into Supabase
    try:
        res = supabase.table("papers").insert(payload).execute()
    except Exception as e:
        print(f"[SYNC ERROR] Insert failed: {e}")
        raise HTTPException(status_code=500, detail="DB insert failed")

    if not res or not res.data:
        raise HTTPException(
            status_code=500, detail="Insert failed: no data returned")

    print(f"[SYNC] ✅ Saved paper {pmid} with ID {res.data[0]['id']}")
    return res.data[0]
