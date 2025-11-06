# routes/biomarkers.py
from fastapi import APIRouter, HTTPException
from utils.db import supabase

router = APIRouter(prefix="/biomarkers", tags=["Biomarkers"])


@router.get("/")
def list_biomarkers():
    """List biomarkers and counts of supporting papers."""
    try:
        res = (
            supabase.table("paper_graph")
            .select("biomarker, mechanism, paper_pmid, edge_type")
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}")

    if not res.data:
        raise HTTPException(status_code=404, detail="No biomarkers found.")

    counts = {}
    for r in res.data:
        if not r:
            continue
        bio = r.get("biomarker")
        mech = r.get("mechanism")
        edge = (r.get("edge_type") or "").lower()

        # include both old and new naming variants
        if edge not in ["mechanism→biomarker", "mechanism->biomarker"]:
            continue
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

    if not biomarkers:
        raise HTTPException(
            status_code=404, detail="No biomarker edges found.")
    return biomarkers
