from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.db import supabase
from utils.openai_client import client
import hashlib
import os
from datetime import datetime
import json

router = APIRouter(prefix="/evidence", tags=["evidence"])


class EvidenceResponse(BaseModel):
    status: str
    summary: str
    mechanisms: list[str]
    biomarkers: list[str]
    confidence: float


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@router.post("/papers/{pmid}/generate")
async def generate_evidence(pmid: str):

    # 1) Fetch paper record
    result = (
        supabase.table("papers")
        .select("pmid, title, abstract")
        .eq("pmid", pmid)
        .maybe_single()
        .execute()
    )
    paper = result.data

    if not paper:
        raise HTTPException(
            status_code=404, detail="Paper not found. Sync first.")

    title = paper.get("title", "")
    abstract = paper.get("abstract", "")

    if not abstract:
        raise HTTPException(status_code=400, detail="Paper has no abstract")

    input_text = f"{title}\n\n{abstract}"
    h = compute_hash(input_text)

    # 2) Check cache
    existing = (
        supabase.table("paper_summaries")
        .select("id, one_sentence, mechanisms, biomarkers, confidence")
        .eq("hash", h)
        .maybe_single()
        .execute()
    )

    if existing.data:
        return {"status": "cached", "summary_id": existing.data["id"], **existing.data}

    # 3) GPT-5 prompt
    prompt = f"""
You are a biomedical mechanistic reasoning system for ME/CFS.

Paper:
Title: {title}
Abstract: {abstract}

Extract:
- One-sentence mechanistic summary
- Mechanisms (immune, mitochondrial, vascular, autonomic, metabolic, endocrine, neurological, viral persistence)
- Biomarkers if mentioned or implied
- Confidence 0–1

Return JSON ONLY in this format:

{{
 "summary": "...",
 "mechanisms": [],
 "biomarkers": [],
 "confidence": 0.00
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)  # ✅ safe parse
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Model parsing failed: {e}")

    row = {
        "paper_pmid": pmid,   # ✅ correct FK
        "one_sentence": parsed["summary"],
        "mechanisms": parsed.get("mechanisms", []),
        "biomarkers": parsed.get("biomarkers", []),
        "confidence": parsed.get("confidence", 0.5),
        "tags": parsed.get("mechanisms", []),
        "hash": h,
        "created_at": datetime.utcnow().isoformat()
    }

    inserted = supabase.table("paper_summaries").insert(row).execute()

    return {"status": "done", "summary_id": inserted.data[0]["id"], **parsed}
