from fastapi import APIRouter, HTTPException
from supabase import create_client
from pydantic import BaseModel
import hashlib
import os
from datetime import datetime
import openai

router = APIRouter(prefix="/evidence", tags=["evidence"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

openai.api_key = os.getenv("OPENAI_API_KEY")


class EvidenceResponse(BaseModel):
    status: str
    mechanisms: list[str]
    biomarkers: list[str]
    confidence: float
    summary: str


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@router.post("/papers/{pmid}/generate")
async def generate_evidence(pmid: str):

    # 1) Fetch paper record
    result = supabase.table("papers").select(
        "*").eq("pmid", pmid).single().execute()
    paper = result.data

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    input_text = f"{title}\n\n{abstract}"

    # 2) Check if already computed
    hash_value = compute_hash(input_text)
    existing = supabase.table("paper_summaries").select(
        "*").eq("hash", hash_value).execute()

    if existing.data:
        return {"status": "cached"}

    # 3) Call GPT-5
    prompt = f"""
You are a biomedical mechanistic reasoning model.

Paper:
Title: {title}
Abstract: {abstract}

Extract:
- one sentence mechanistic summary
- key mechanisms (immune, mitochondrial, vascular, autonomic, metabolic, endocrine, neurological)
- any biomarkers mentioned or implied
- confidence 0–1

Return JSON:
{{
 "summary": "...",
 "mechanisms": [],
 "biomarkers": [],
 "confidence": 0.00
}}
    """

    response = openai.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": prompt}]
    )

    data = response.choices[0].message.content
    parsed = eval(data)  # ✅ GPT returns clean JSON here

    # 4) Insert row
    supabase.table("paper_summaries").insert({
        "paper_pmid": pmid,
        "one_sentence": parsed["summary"],
        "mechanisms": parsed["mechanisms"],
        "biomarkers": parsed["biomarkers"],
        "confidence": parsed["confidence"],
        "hash": hash_value,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return {"status": "done", **parsed}
