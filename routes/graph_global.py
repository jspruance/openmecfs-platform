# routes/graph_global.py
from fastapi import APIRouter
from utils.db import supabase

router = APIRouter(prefix="/graph", tags=["graph"])

# Core ME/CFS mechanism families
MECH_GROUPS = {
    "immune": ["immune", "inflammation", "cytokine", "t-cell", "autoimmune"],
    "mitochondrial": ["mito", "oxidative", "redox", "energy", "metabolic"],
    "vascular": ["endothelial", "vascular", "microclot", "blood flow"],
    "autonomic": ["dysautonomia", "pots", "autonomic", "orthostatic"],
    "neuroinflammation": ["neuro", "brain", "microglia", "neuroinflammation"],
    "viral": ["viral", "persistent", "post-viral", "ebv", "hhv6"],
}


def categorize_mech(mech: str):
    mech_l = mech.lower()
    for group, keywords in MECH_GROUPS.items():
        if any(k in mech_l for k in keywords):
            return group
    return "other"


@router.get("/global")
def global_graph(limit: int = 300):
    res = (
        supabase.table("paper_summaries")
        .select("paper_pmid, mechanisms, one_sentence, confidence")
        .limit(limit)
        .execute()
    )

    nodes = []
    links = []
    seen = set()

    # Add mechanism hubs first
    for mech_group in MECH_GROUPS.keys():
        hub_id = f"hub:{mech_group}"
        nodes.append({
            "id": hub_id,
            "label": mech_group.title(),
            "type": "hub"
        })
        seen.add(hub_id)

    awaiting = []  # orphan papers (no mechanism)

    for row in res.data or []:
        pmid = row.get("paper_pmid")
        mechs = row.get("mechanisms") or []
        sentence = row.get("one_sentence", "")
        confidence = row.get("confidence", None)

        if not pmid:
            continue

        if pmid not in seen:
            nodes.append({
                "id": pmid,
                "label": pmid,
                "title": sentence[:90] + "…" if sentence else "",
                "confidence": confidence,
                "type": "paper"
            })
            seen.add(pmid)

        if not mechs:
            awaiting.append(pmid)
            continue

        for mech in mechs:
            mech = mech.strip()
            if not mech:
                continue

            group = categorize_mech(mech)
            hub_id = f"hub:{group}"

            links.append({
                "source": pmid,
                "target": hub_id,
                "type": "paper→mechanism"
            })

    return {
        "nodes": nodes,
        "links": links,
        "awaiting": awaiting
    }
