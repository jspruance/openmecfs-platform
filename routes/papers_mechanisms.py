# routes/papers_mechanisms.py
"""
Open ME/CFS — Mechanistic Evidence Extraction (Hybrid)
------------------------------------------------------------
Purpose:
    Extract mechanistic evidence from a paper's abstract using a hybrid schema:
      - Fixed categories (for analytics/graph)
      - Free-text mechanisms (for rich detail)
      - Biomarkers (molecules/cells)
      - Confidence + raw model JSON

Flow:
    Supabase `papers` (sync first) -> /papers/mechanisms/{pmid}
      -> GPT-5 hybrid extraction -> upsert `paper_mechanisms`

One row per (pmid, provider, model).
"""

from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.openai import client
import json

router = APIRouter(prefix="/papers", tags=["Mechanisms"])

FIXED_CATEGORIES = [
    "immune", "mitochondrial", "vascular", "autonomic",
    "neurological", "metabolic", "oxidative_stress", "infectious_trigger"
]

SYSTEM_PROMPT = f"""You are a biomedical model extracting ME/CFS mechanistic evidence.

Return STRICT JSON with keys:
- categories: array of strings chosen ONLY from: {FIXED_CATEGORIES}
- mechanisms: array of concise free-text mechanism statements
- biomarkers: array of concise biomarker terms (molecules/cells)
- confidence: number between 0 and 1 (float)

Rules:
- Use categories ONLY from the fixed list; if none fit, return [].
- mechanisms should be 1–8 short items max, specific (e.g., "NK cytotoxicity deficit").
- biomarkers should be 0–12 items, specific (e.g., "IL-6", "NK cells", "ATP", "ET-1").
- If uncertain, reduce confidence and keep arrays minimal.
- No commentary, ONLY JSON object.
"""


@router.post("/mechanisms/{pmid}")
def extract_mechanisms(pmid: str):
    # 1) Fetch paper
    paper_q = (
        supabase.table("papers")
        .select("*")
        .eq("pmid", pmid)
        .maybe_single()
        .execute()
    )
    if not paper_q or not getattr(paper_q, "data", None):
        raise HTTPException(
            status_code=404, detail="Paper not found; run /papers/sync/{pmid} first.")

    paper = paper_q.data
    abstract = (paper.get("abstract") or "").strip()
    if not abstract:
        raise HTTPException(
            status_code=400, detail="Paper has no abstract; cannot extract mechanisms.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": abstract},
    ]

    # 2) Call OpenAI
    try:
        resp = client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    # 3) Parse + validate
    try:
        # already parsed object via response_format
        parsed = resp.choices[0].message.parsed
        # Ensure keys exist
        categories = parsed.get("categories", []) or []
        mechanisms = parsed.get("mechanisms", []) or []
        biomarkers = parsed.get("biomarkers", []) or []
        confidence = float(parsed.get("confidence", 0.0) or 0.0)

        # Coerce to lists of strings
        categories = [str(x).strip() for x in categories if str(x).strip()]
        mechanisms = [str(x).strip() for x in mechanisms if str(x).strip()]
        biomarkers = [str(x).strip() for x in biomarkers if str(x).strip()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse error: {e}")

    # 4) Upsert into paper_mechanisms
    row = {
        "pmid": pmid,
        # Foreign key to papers table using pmid
        "paper_pmid": pmid,
        "categories": categories,
        "mechanisms": mechanisms,
        "biomarkers": biomarkers,
        "confidence": confidence,
        "provider": "openai",
        "model": "gpt-5",
        "raw_output": parsed,
    }

    try:
        # One row per (pmid, provider, model)
        res = supabase.table("paper_mechanisms").upsert(
            row, on_conflict="pmid,provider,model").execute()
    except Exception:
        # Some supabase-py versions lack on_conflict; fallback: delete then insert
        supabase.table("paper_mechanisms").delete().match(
            {"pmid": pmid, "provider": "openai", "model": "gpt-5"}).execute()
        res = supabase.table("paper_mechanisms").insert(row).execute()

    if not res or not res.data:
        raise HTTPException(
            status_code=500, detail="Failed to store mechanisms.")

    return {
        "pmid": pmid,
        "categories": categories,
        "mechanisms": mechanisms,
        "biomarkers": biomarkers,
        "confidence": confidence,
        "stored": True,
    }
