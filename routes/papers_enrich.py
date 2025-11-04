from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.openai_client import client  # your wrapper
import json

router = APIRouter(prefix="/papers", tags=["papers"])

SYSTEM = """
You are an ME/CFS research analysis model.
Given the abstract and title, extract:

- one sentence mechanistic insight
- list of biological mechanisms (controlled vocab)
- biomarkers mentioned
- 0-1 confidence score

Return valid JSON with keys:
one_sentence, mechanisms, biomarkers, confidence
"""

CONTROLLED_MECHANISMS = [
    "immune dysfunction",
    "mitochondrial dysfunction",
    "vascular / endothelial dysfunction",
    "viral persistence / reactivation",
    "autonomic dysfunction",
    "oxidative stress / redox imbalance",
    "metabolic dysregulation",
    "neuroinflammation",
    "microbiome / gut dysbiosis"
]


@router.post("/enrich/{pmid}")
def enrich_paper(pmid: str):
    paper = (
        supabase.table("papers")
        .select("pmid,title,abstract")
        .eq("pmid", pmid)
        .single()
        .execute()
    ).data

    if not paper:
        raise HTTPException(404, f"Paper {pmid} not found")

    prompt = f"""
Paper title: {paper['title']}
Abstract: {paper['abstract']}

Allowed mechanism tags:
{json.dumps(CONTROLLED_MECHANISMS, indent=2)}

Return JSON only.
"""

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ]
    )

    try:
        out = json.loads(resp.choices[0].message.content)
    except:
        raise HTTPException(500, "Model returned invalid JSON")

    supabase.table("paper_summaries").upsert({
        "paper_pmid": pmid,
        "one_sentence": out.get("one_sentence"),
        "mechanisms": out.get("mechanisms"),
        "biomarkers": out.get("biomarkers"),
        "confidence": out.get("confidence"),
    }).execute()

    return {"pmid": pmid, "result": out, "status": "saved"}
