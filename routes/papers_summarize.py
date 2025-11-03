# routes/papers_summarize.py

from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.openai_client import client
import hashlib
import datetime
import json
import traceback

router = APIRouter(prefix="/papers", tags=["AI Summaries"])

SYSTEM_PROMPT = """
You are an expert biomedical research analyst specializing in ME/CFS and post-viral illness.
Return a structured mechanistic summary ONLY based on the text provided.

Return VALID JSON with keys:
- one_sentence
- technical_summary
- patient_summary
- mechanisms (array)
- biomarkers (array)
- confidence (0 to 1)
"""


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@router.post("/summarize/{pmid}")
async def summarize_paper(pmid: str):

    paper = (
        supabase.table("papers")
        .select("*")
        .eq("pmid", pmid)
        .maybe_single()
        .execute()
    )

    if not paper or not paper.data:
        raise HTTPException(
            status_code=404, detail="Paper not found. Sync first.")

    paper = paper.data
    text = (paper.get("title") or "") + "\n\n" + (paper.get("abstract") or "")
    text = text.strip() or f"(No abstract) {paper.get('title', '')}"

    hash_value = compute_hash(text)
    existing = supabase.table("paper_summaries").select(
        "id").eq("hash", hash_value).execute()
    if existing.data:
        return {"status": "cached", "pmid": pmid}

    try:
        resp = await client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
        )

        try:
            ai = resp.choices[0].message.parsed
        except:
            ai = json.loads(resp.choices[0].message.content)

    except Exception as e:
        raise HTTPException(500, {
            "error": "OpenAI failure",
            "exception": str(e),
            "trace": traceback.format_exc(),
        })

    supabase.table("paper_summaries").insert({
        "paper_pmid": pmid,  # ✅ correct FK
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


@router.get("/summaries/{pmid}")
async def get_summary(pmid: str):
    result = (
        supabase.table("paper_summaries")
        .select("*")
        .eq("paper_pmid", pmid)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    # No summary yet
    if not result.data:
        return {"status": "not summarized", "pmid": pmid}

    return result.data[0]
