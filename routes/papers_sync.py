from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.europepmc import fetch_paper_by_pmid
import asyncio

router = APIRouter(prefix="/papers", tags=["Papers"])


@router.post("/sync/{pmid}")
async def sync_paper(pmid: str):
    """
    Sync a paper from EuropePMC into Supabase `papers` table.
    If it already exists, return the existing row.
    """

    print(f"[SYNC] Checking Supabase for PMID {pmid}")

    # 1️⃣ Check if paper already exists
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

    if existing and getattr(existing, "data", None):
        print(f"[SYNC] ✅ Found cached paper for PMID {pmid}")
        return existing.data

    # 2️⃣ Fetch metadata from EuropePMC
    print(f"[SYNC] Fetching from EuropePMC for PMID {pmid}")

    try:
        if asyncio.iscoroutinefunction(fetch_paper_by_pmid):
            data = await fetch_paper_by_pmid(pmid)
        else:
            data = fetch_paper_by_pmid(pmid)
    except Exception as e:
        print(f"[SYNC ERROR] EuropePMC fetch failed: {e}")
        raise HTTPException(status_code=500, detail="EuropePMC fetch failed")

    if not data:
        raise HTTPException(
            status_code=404, detail=f"PMID {pmid} not found on EuropePMC"
        )

    # 3️⃣ Normalize + upsert
    payload = {
        "pmid": pmid,
        "title": (data.get("title") or "").strip(),
        "abstract": (data.get("abstract") or "").strip(),
        "journal": (data.get("journal") or "").strip(),
        "year": data.get("year") or None,
        "authors": data.get("authors", []),
        "authors_text": data.get("authors_text"),
    }

    print(f"[SYNC] Upserting into Supabase... {payload}")

    try:
        res = supabase.table("papers").upsert(payload).execute()
    except Exception as e:
        print(f"[SYNC ERROR] Upsert failed: {e}")
        raise HTTPException(status_code=500, detail="DB upsert failed")

    if not res or not res.data:
        raise HTTPException(
            status_code=500, detail="Upsert failed: no data returned"
        )

    print(f"[SYNC] ✅ Saved paper {pmid}")
    return res.data[0]
