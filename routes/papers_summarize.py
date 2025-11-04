# routes/papers_summarize.py

from fastapi import APIRouter, HTTPException
from utils.db import supabase
from utils.openai_client import client
import hashlib
import datetime
import json
import traceback
import re

router = APIRouter(prefix="/papers", tags=["AI Summaries"])

# ✅ Controlled mechanism ontology
VALID_MECHANISMS = {
    "immune dysregulation",
    "mitochondrial dysfunction",
    "oxidative stress",
    "vascular / endothelial dysfunction",
    "autonomic dysfunction / POTS",
    "viral persistence",
    "neuroinflammation",
    "microbiome dysbiosis",
    "energy metabolism abnormalities",
}

SYSTEM_PROMPT = """
You are an expert biomedical research analyst specializing in ME/CFS.

Return STRICT JSON only with:

- one_sentence
- technical_summary
- patient_summary
- mechanisms (array of strings)
- biomarkers (array of strings)
- confidence (0-1 float)

Rules:
- Choose mechanisms ONLY from this list:

IMMUNE DYSREGULATION,
MITOCHONDRIAL DYSFUNCTION,
OXIDATIVE STRESS,
VASCULAR / ENDOTHELIAL DYSFUNCTION,
AUTONOMIC DYSFUNCTION / POTS,
VIRAL PERSISTENCE,
NEUROINFLAMMATION,
MICROBIOME DYSBIOSIS,
ENERGY METABOLISM ABNORMALITIES

- Biomarkers must be real biological markers (proteins, metabolites, immune markers).
- Do NOT invent biomarkers.
- Keep strings clean, short, standardized.
"""


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def clean_list(items):
    """Normalize and validate list entries"""
    cleaned = []
    for x in items or []:
        if not isinstance(x, str):
            continue
        x = x.strip()
        if not x:
            continue
        x = re.sub(r"[^a-zA-Z0-9\- /]", "", x)
        if len(x) < 2:
            continue
        cleaned.append(x)
    return list(dict.fromkeys(cleaned))  # unique + keep order


async def store_graph(pmid: str, mechs: list, biomarkers: list):
    """Store paper → mechanism → biomarker edges"""
    for m in mechs:
        await supabase.table("paper_graph").insert({
            "paper_pmid": pmid,
            "mechanism": m,
            "edge_type": "paper→mechanism",
        }).execute()

        for b in biomarkers:
            await supabase.table("paper_graph").insert({
                "paper_pmid": pmid,
                "mechanism": m,
                "biomarker": b,
                "edge_type": "mechanism→biomarker",
            }).execute()


@router.post("/summarize/{pmid}")
async def summarize_paper(pmid: str):

    paper = supabase.table("papers").select(
        "*").eq("pmid", pmid).maybe_single().execute()
    if not paper or not paper.data:
        raise HTTPException(404, "Paper not found. Sync first.")

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
        raise HTTPException(
            500, {"error": str(e), "trace": traceback.format_exc()})

    # ✅ normalize mechanisms
    mechs_raw = clean_list(ai.get("mechanisms")
                           or [])
    mechs = [m.lower() for m in mechs_raw if m.lower() in VALID_MECHANISMS]

    # ✅ clean biomarkers
    biomarkers = clean_list(ai.get("biomarkers"))

    # ✅ store summary
    supabase.table("paper_summaries").insert({
        "paper_pmid": pmid,
        "provider": "openai",
        "model": "gpt-5",
        "one_sentence": ai.get("one_sentence", ""),
        "technical_summary": ai.get("technical_summary", ""),
        "patient_summary": ai.get("patient_summary", ""),
        "mechanisms": mechs,
        "biomarkers": biomarkers,
        "confidence": ai.get("confidence"),
        "hash": hash_value,
        "created_at": datetime.datetime.utcnow().isoformat()
    }).execute()

    supabase.table("papers").update({
        "summarized_at": datetime.datetime.utcnow().isoformat()
    }).eq("pmid", pmid).execute()

    await store_graph(pmid, mechs, biomarkers)

    # ✅ return clean data
    return {
        "status": "done",
        "pmid": pmid,
        **ai,
        "mechanisms": mechs,
        "biomarkers": biomarkers
    }
