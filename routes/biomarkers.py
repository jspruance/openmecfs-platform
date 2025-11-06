# routes/biomarkers.py
from fastapi import APIRouter, HTTPException
from utils.db import supabase

router = APIRouter(prefix="/biomarkers", tags=["Biomarkers"])


@router.get("")
def list_biomarkers():
    """List biomarkers and counts of supporting papers."""
    res = (
        supabase.table("paper_graph")
        .select("biomarker, mechanism, paper_pmid")
        .eq("edge_type", "mechanism→biomarker")
        .execute()
    )

    if not res.data:
        raise HTTPException(404, "No biomarkers found.")

    counts = {}
    for r in res.data:
        bio = r["biomarker"]
        mech = r.get("mechanism")
        if not bio:
            continue
        if bio not in counts:
            counts[bio] = {"count": 0, "mechanisms": set()}
        counts[bio]["count"] += 1
        if mech:
            counts[bio]["mechanisms"].add(mech)

    biomarkers = sorted(
        [
            {
                "biomarker": b,
                "count": v["count"],
                "mechanisms": sorted(list(v["mechanisms"])),
            }
            for b, v in counts.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    return biomarkers
