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

If information is absent, return empty lists/strings. NO extra fields. NO commentary.
"""


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@router.post("/summarize/{pmid}")
async def summarize_paper(pmid: str):

    # 1️⃣ Fetch paper metadata
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
    abstract = (paper.get("abstract") or "").strip()
    title = (paper.get("title") or "").strip()

    if abstract:
        text = f"{title}\n\n{abstract}"
    elif title:
        text = f"(No abstract available)\n{title}"
    else:
        return {"status": "no-text", "pmid": pmid}

    # 2️⃣ Cache hash
    hash_value = compute_hash(text)
    existing = (
        supabase.table("paper_summaries")
        .select("*")
        .eq("hash", hash_value)
        .execute()
    )
    if existing.data:
        return {"status": "cached", "pmid": pmid}

    # 3️⃣ OpenAI call
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
        raise HTTPException(
            status_code=500,
            detail={
                "error": "OpenAI call or JSON parse failed",
                "exception": str(e),
                "trace": traceback.format_exc(),
                "pmid": pmid
            }
        )

    # 4️⃣ Store summary (✅ Correct FK)
    supabase.table("paper_summaries").insert({
        "paper_id": paper["paper_id"],   # ✅ correct foreign key field
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

    # 5️⃣ Mark parent paper as summarized
    supabase.table("papers").update({
        "summarized_at": datetime.datetime.utcnow().isoformat()
    }).eq("pmid", pmid).execute()

    return {"status": "done", "pmid": pmid, **ai}
