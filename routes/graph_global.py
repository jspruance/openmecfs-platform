# routes/graph_global.py
from fastapi import APIRouter
from utils.db import supabase

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/global")
def global_graph(limit: int = 300):
    """
    Returns global graph: papers ↔ mechanisms
    """

    # Fetch papers + linked mechanisms
    papers_res = (
        supabase.table("paper_summaries")
        .select("paper_pmid, mechanisms")
        .limit(limit)
        .execute()
    )

    nodes = []
    links = []

    seen_nodes = set()

    for row in papers_res.data or []:
        pmid = row.get("paper_pmid")
        mechs = row.get("mechanisms") or []

        if not pmid:
            continue

        # Add paper node
        if pmid not in seen_nodes:
            nodes.append({
                "id": pmid,
                "label": pmid,
                "type": "paper"
            })
            seen_nodes.add(pmid)

        for mech in mechs:
            mech = mech.strip()
            if not mech:
                continue

            if mech not in seen_nodes:
                nodes.append({
                    "id": mech,
                    "label": mech,
                    "type": "mechanism"
                })
                seen_nodes.add(mech)

            links.append({
                "source": pmid,
                "target": mech,
                "type": "paper-mechanism"
            })

    return {"nodes": nodes, "links": links}
