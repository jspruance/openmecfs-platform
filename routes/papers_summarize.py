# routes/papers_summarize.py
"""
Open ME/CFS — AI Paper Summarization Router
Generates structured mechanistic summaries for stored papers.
"""

from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.openai_client import client  # ✅ correct client
import hashlib
import datetime

router = APIRouter(prefix="/papers", tags=["AI Summaries"])


SYSTEM_PROMPT = """
You are a biomedical literature analyst for ME/CFS and post-viral disease research.
Extract mechanistic insight without speculation.

Return a JSON object:

{
 "one_sentence": "...",
 "technical_summary": "...",
 "patient_summary": "...",
 "mechanisms": ["immune", "mitochondrial", "vascular", "autonomic", "neurological", "endocrine"],
 "biomarkers": ["IL-6", "ATP", "NK cells", "VEGF"],
 "confidence": 0.00
}

Mechanisms = high-level biological systems.
Biomarkers = specific measurable molecules/cell types.
If not present, return empty list.
"""


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@router.post("/summarize/{pmid}")
def summarize_paper(pmid: str):
    # 1️⃣ Get paper
    paper = (
        supabase.table("papers")
        .select("*")
        .eq("pmid", pmid)
        .maybe_single()
        .execute()
    )

    if not paper or not getattr(paper, "data", None):
        raise HTTPException(
            status_code=404, detail="Paper not found. Sync first.")

    paper = paper.data
    abstract = (paper.get("abstract") or "").strip()
    title = (paper.get("title") or "").strip()

    if not abstract:
        raise HTTPException(status_code=400, detail="Paper has no abstract.")

    input_text = title + "\n\n" + abstract
    hash_value = compute_hash(input_text)

    # 2️⃣ Skip if already summarized
    exists = (
        supabase.table("paper_summaries")
        .select("*")
        .eq("hash", hash_value)
        .execute()
    )

    if exists.data:
        return {"status": "cached", "pmid": pmid}

    # 3️⃣ Call OpenAI
    try:
        resp = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": input_text}
            ],
            response_format={"type": "json_object"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    ai = resp.choices[0].message.parsed

    # 4️⃣ Save to DB
    supabase.table("paper_summaries").insert({
        "paper_pmid": pmid,                     # ✅ matches schema
        "provider": "openai",
        "model": "gpt-5",
        "one_sentence": ai["one_sentence"],
        "technical_summary": ai["technical_summary"],
        "patient_summary": ai["patient_summary"],
        "mechanisms": ai.get("mechanisms", []),
        "biomarkers": ai.get("biomarkers", []),
        "confidence": ai.get("confidence", None),
        "hash": hash_value,
        "created_at": datetime.datetime.utcnow().isoformat()
    }).execute()

    # 5️⃣ Update paper timestamp
    supabase.table("papers").update({
        "summarized_at": datetime.datetime.utcnow().isoformat()
    }).eq("pmid", pmid).execute()

    return {"status": "done", "pmid": pmid, **ai}
