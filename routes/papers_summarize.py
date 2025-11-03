# routes/papers_summarize.py

from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.openai import client  # we'll create this next
import datetime

router = APIRouter(prefix="/papers", tags=["AI Summaries"])

SYSTEM_PROMPT = """You are a biomedical research summarization model for ME/CFS.
Goal: extract mechanistic insight, avoid speculation.

Output MUST be valid JSON:

{
 "one_sentence": "...",
 "technical_summary": "...",
 "patient_summary": "...",
 "mechanisms": ["immune", "vascular", "mitochondrial", ...],
 "biomarkers": ["IL-6", "ATP", "NK cells", ...]
}

Rules:
- mechanisms: high-level buckets only
- biomarkers: specific molecules/cell types
- If unsure, return empty list.
"""


@router.post("/summarize/{pmid}")
def summarize_paper(pmid: str):
    # pull paper
    paper = (
        supabase.table("papers")
        .select("*")
        .eq("pmid", pmid)
        .maybe_single()
        .execute()
    )

    if not paper or not getattr(paper, "data", None):
        raise HTTPException(
            status_code=404, detail="Paper not found, sync first")

    paper = paper.data
    text = (paper.get("abstract") or "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="Paper has no abstract")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]

    try:
        resp = client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            response_format={"type": "json_object"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    ai = resp.choices[0].message.parsed

    # store in paper_summaries table
    row = {
        "paper_id": paper["id"],
        "provider": "openai",
        "model": "gpt-5",
        "one_sentence": ai["one_sentence"],
        "technical_summary": ai["technical_summary"],
        "patient_summary": ai["patient_summary"],
        "mechanisms": ai.get("mechanisms", []),
        "biomarkers": ai.get("biomarkers", []),
    }

    supabase.table("paper_summaries").insert(row).execute()

    # update paper record timestamp
    supabase.table("papers").update({
        "summarized_at": datetime.datetime.utcnow().isoformat()
    }).eq("pmid", pmid).execute()

    return ai
