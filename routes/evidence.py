# routes/evidence.py

from fastapi import APIRouter, HTTPException
from uuid import UUID
import hashlib
from utils.openai_client import generate_evidence_summary
from utils.db import fetch_paper_by_id, insert_paper_summary, find_summary_by_hash

router = APIRouter(prefix="/evidence", tags=["Evidence Engine"])


@router.post("/papers/{paper_id}/generate")
async def generate_evidence_for_paper(paper_id: UUID):
    # 1️⃣ Get paper & abstract from DB
    paper = await fetch_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    abstract = paper["abstract"]
    if not abstract:
        raise HTTPException(status_code=400, detail="Paper has no abstract")

    # 2️⃣ Create hash (idempotency key)
    hash_key = hashlib.sha256(abstract.encode("utf-8")).hexdigest()

    # 3️⃣ See if we already have a summary
    existing = await find_summary_by_hash(hash_key)
    if existing:
        return {
            "status": "cached",
            "summary": existing,
        }

    # 4️⃣ Generate evidence via LLM
    summary = await generate_evidence_summary(abstract)

    # 5️⃣ Persist to DB
    saved = await insert_paper_summary(
        paper_id=paper_id,
        summary=summary,
        hash_key=hash_key
    )

    return {
        "status": "generated",
        "summary": saved
    }
