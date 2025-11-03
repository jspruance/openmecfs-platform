# routes/papers_summarize.py

from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.openai_client import client
import hashlib
import datetime
import json

router = APIRouter(prefix="/papers", tags=["AI Summaries"])

SYSTEM_PROMPT = """
You are a biomedical literature analyst for ME/CFS and post-viral disease research.
Extract mechanistic insight without speculation.

Return JSON with keys:
one_sentence, technical_summary, patient_summary, mechanisms, biomarkers, confidence
"""


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@router.post("/summarize/{pmid}")
async def summarize_paper(pmid: str):

    # Fetch paper
    paper = (
        supabase.table("papers")
        .select("*")
        .eq("pmid", pmid)
        .maybe_single()
        .execute()
    )

    if not paper or not paper.data:
        raise HTTPException(404, "Paper not found. Sync first.")

    paper = paper.data
    abstract = (paper.get("abstract") or "").strip()
    title = (paper.get("title") or "").strip()

    # Fallback for title-only papers
    text = f"{title}\n\n{abstract}" if abstract else f"(No abstract) {title}"
    hash_value = compute_hash(text)

    # Skip if already summarized
    existing = (
        supabase.table("paper_summaries")
        .select("*")
        .eq("hash", hash_value)
        .execute()
    )
    if existing.data:
        return {"status": "cached", "pmid": pmid}

    # ✅ OpenAI call (async)
    try:
        response = await client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"}
        )

        # SDK v1 "parsed" helper (when present)
        try:
            ai = response.choices[0].message.parsed
        except:
            ai = json.loads(response.choices[0].message.content)

    except Exception as e:
        raise HTTPException(500, f"OpenAI failed: {e}")

    # ✅ Store result
    supabase.table("paper_summaries").insert({
        "paper_pmid": pmid,
        "provider": "openai",
        "model": "gpt-5",
        "one_sentence": ai.get("one_sentence", ""),
        "technical_summary": ai.get("technical_summary", ""),
        "patient_summary": ai.get("patient_summary", ""),
        "mechanisms": ai.get("mechanisms", []),
        "biomarkers": ai.get("biomarkers", []),
        "confidence": ai.get("confidence", None),
        "hash": hash_value,
        "created_at": datetime.datetime.utcnow().isoformat()
    }).execute()

    supabase.table("papers").update({
        "summarized_at": datetime.datetime.utcnow().isoformat()
    }).eq("pmid", pmid).execute()

    return {"status": "done", "pmid": pmid, **ai}
