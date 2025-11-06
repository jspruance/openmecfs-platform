from fastapi import APIRouter, HTTPException
from utils.db import supabase

router = APIRouter(prefix="/biomarkers", tags=["Biomarkers"])


@router.get("/graph")
def biomarker_graph():
    """Return nodes and links for biomarkers ↔ mechanisms"""
    try:
        res = (
            supabase.table("paper_graph")
            .select("mechanism, biomarker, edge_type")
            .execute()
        )
        rows = [r for r in res.data if r.get(
            "mechanism") and r.get("biomarker")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    nodes, links = {}, []

    for row in rows:
        mech = row["mechanism"].strip()
        biom = row["biomarker"].strip()

        if mech not in nodes:
            nodes[mech] = {"id": mech, "type": "mechanism", "val": 5}
        if biom not in nodes:
            nodes[biom] = {"id": biom, "type": "biomarker", "val": 2}

        links.append({"source": mech, "target": biom,
                     "type": "mechanism→biomarker"})

    return {"nodes": list(nodes.values()), "links": links}
