from fastapi import APIRouter
from utils.db import supabase
from collections import defaultdict

# ✅ Mechanism ontology mapping
ONTOLOGY = {
    "Immune dysregulation": [
        "immune", "t cell", "b cell", "nk cell",
        "autoimmunity", "cytokine", "inflammation"
    ],
    "Mitochondrial impairment": [
        "mitochondria", "mitochondrial", "atp", "oxidative phosphorylation",
        "energy metabolism"
    ],
    "Vascular / Endothelial dysfunction": [
        "endothelial", "vascular", "blood flow", "perfusion", "microcirculation"
    ],
    "Autonomic dysfunction (POTS/ANS)": [
        "autonomic", "pots", "orthostatic", "adrenergic", "heart rate"
    ],
    "Oxidative stress / Redox imbalance": [
        "oxidative", "radical", "nitrosative", "ros", "redox"
    ],
    "Viral / Immune Trigger": [
        "ebv", "virus", "viral", "infection", "post-viral"
    ],
    "Metabolic dysfunction": [
        "metabolism", "metabolic", "glucose", "lactate", "pyruvate"
    ]
}


def canonicalize(mech: str):
    m = mech.lower().strip()

    # Ignore ultra-long & nonsense strings
    if len(m) > 64:
        return None

    for canonical, variants in ONTOLOGY.items():
        for v in variants:
            if v.lower() in m:
                return canonical

    return None  # drop unmatched noisy terms


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/global")
def global_graph(limit: int = 300):
    """
    Returns global graph: papers ↔ mechanisms (canonicalized)
    """

    res = (
        supabase.table("paper_summaries")
        .select("paper_pmid, mechanisms")
        .limit(limit)
        .execute()
    )

    nodes = []
    links = []
    seen = set()

    for row in res.data or []:
        pmid = row.get("paper_pmid")
        raw_mechs = row.get("mechanisms") or []

        if not pmid:
            continue

        # ✅ Paper node
        if pmid not in seen:
            nodes.append({"id": pmid, "label": pmid, "type": "paper"})
            seen.add(pmid)

        for mech in raw_mechs:
            mech = mech.strip()
            if not mech:
                continue

            canonical = canonicalize(mech)
            if not canonical:
                continue  # skip noise

            if canonical not in seen:
                nodes.append({
                    "id": canonical,
                    "label": canonical,
                    "type": "mechanism"
                })
                seen.add(canonical)

            links.append({
                "source": pmid,
                "target": canonical,
                "type": "paper-mechanism"
            })

    return {"nodes": nodes, "links": links}
