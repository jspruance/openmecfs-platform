# routes/graph.py
from fastapi import APIRouter, Query
from utils.db import supabase

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
def global_graph(limit: int = Query(200, ge=10, le=2000)):
    """
    Build a simple tripartite graph:
      - paper:<pmid>
      - mech:<mechanism>
      - bio:<biomarker>
    Links:
      - paper -> mech
      - paper -> bio
    """
    # pull the latest N summaries
    res = (
        supabase.table("paper_summaries")
        .select("paper_pmid, mechanisms, biomarkers, created_at, one_sentence")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = res.data or []

    nodes = {}
    links = []
    paper_meta = {}  # store one_sentence for tooltip

    def add_node(node_id, label, ntype):
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": ntype,
                "size": 1,
            }
        else:
            nodes[node_id]["size"] += 1

    for r in rows:
        pmid = r.get("paper_pmid")
        if not pmid:
            continue
        paper_id = f"paper:{pmid}"
        add_node(paper_id, pmid, "paper")
        paper_meta[paper_id] = r.get("one_sentence") or ""

        for m in (r.get("mechanisms") or []):
            m = (m or "").strip()
            if not m:
                continue
            mech_id = f"mech:{m}"
            add_node(mech_id, m, "mechanism")
            links.append(
                {"source": paper_id, "target": mech_id, "type": "paper-mech"})

        for b in (r.get("biomarkers") or []):
            b = (b or "").strip()
            if not b:
                continue
            bio_id = f"bio:{b}"
            add_node(bio_id, b, "biomarker")
            links.append(
                {"source": paper_id, "target": bio_id, "type": "paper-bio"})

    # convert to arrays + attach meta
    node_list = list(nodes.values())
    for n in node_list:
        if n["type"] == "paper":
            n["meta"] = {"one_sentence": paper_meta.get(n["id"], "")}

    return {"nodes": node_list, "links": links}


@router.get("/paper/{pmid}")
def paper_graph(pmid: str):
    """
    Mini graph for a single paper: paper node + its mechanisms/biomarkers
    """
    res = (
        supabase.table("paper_summaries")
        .select("mechanisms, biomarkers, one_sentence, created_at")
        .eq("paper_pmid", pmid)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return {"nodes": [], "links": []}

    r = rows[0]
    nodes = [{"id": f"paper:{pmid}", "label": pmid, "type": "paper", "size": 3,
              "meta": {"one_sentence": r.get("one_sentence", "")}}]
    links = []

    for m in (r.get("mechanisms") or []):
        m = (m or "").strip()
        if not m:
            continue
        nodes.append({"id": f"mech:{m}", "label": m,
                     "type": "mechanism", "size": 1})
        links.append({"source": f"paper:{pmid}",
                     "target": f"mech:{m}", "type": "paper-mech"})

    for b in (r.get("biomarkers") or []):
        b = (b or "").strip()
        if not b:
            continue
        nodes.append({"id": f"bio:{b}", "label": b,
                     "type": "biomarker", "size": 1})
        links.append({"source": f"paper:{pmid}",
                     "target": f"bio:{b}", "type": "paper-bio"})

    return {"nodes": nodes, "links": links}
