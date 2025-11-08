from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from openai import OpenAI
import os
import uuid
import re
import json
from sentence_transformers import SentenceTransformer, util

# --------------------------------------------------------------------
# 🧠 Initialization
# --------------------------------------------------------------------
router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)

# Load lightweight embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# --------------------------------------------------------------------
# 🔍 Text normalization
# --------------------------------------------------------------------


def normalize_title(title: str) -> str:
    if not title:
        return ""
    t = title.lower()
    t = re.sub(r"[^a-z0-9 ]+", "", t)
    t = re.sub(r"\b(me/cfs|mecfs|chronic fatigue syndrome)\b", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

# --------------------------------------------------------------------
# 🧩 Semantic Deduplication via Embeddings
# --------------------------------------------------------------------


def deduplicate_semantically(hypotheses, threshold: float = 0.85):
    if len(hypotheses) <= 1:
        return hypotheses

    titles = [normalize_title(h.get("title", "")) for h in hypotheses]
    embeddings = model.encode(
        titles, convert_to_tensor=True, normalize_embeddings=True)

    keep = []
    used = set()

    for i, h in enumerate(hypotheses):
        if i in used:
            continue
        group = [i]
        for j in range(i + 1, len(hypotheses)):
            if j in used:
                continue
            sim = float(util.cos_sim(embeddings[i], embeddings[j]))
            if sim >= threshold:
                used.add(j)
                group.append(j)

        # Keep the first hypothesis in each semantic cluster
        keep.append(h)

    print(f"🧩 Deduplicated {len(hypotheses)} → {len(keep)} unique hypotheses")
    return keep


# --------------------------------------------------------------------
# 🚀 Combined Hypotheses Endpoint
# --------------------------------------------------------------------
@router.get("/hypotheses")
async def get_ai_hypotheses():
    """
    Returns both:
      1. Seeded hypotheses stored in Supabase (ai_hypotheses table)
      2. Live AI-generated hypotheses derived from paper_summaries
         with semantic deduplication
    """
    try:
        # ----------------------------------------------------------------
        # 1️⃣ Pull existing hypotheses (seeded or previously saved)
        # ----------------------------------------------------------------
        seeded = (
            supabase.table("ai_hypotheses")
            .select("*")
            .order("created_at", desc=True)
            .execute()
            .data
        )

        # ----------------------------------------------------------------
        # 2️⃣ Gather recent paper summaries
        # ----------------------------------------------------------------
        summaries = (
            supabase.table("paper_summaries")
            .select("one_sentence")
            .limit(40)
            .execute()
            .data
        )
        if not summaries:
            return deduplicate_semantically(seeded or [])

        text_corpus = "\n".join(f"- {s['one_sentence']}" for s in summaries)

        # ----------------------------------------------------------------
        # 3️⃣ Ask GPT for new hypotheses
        # ----------------------------------------------------------------
        prompt = f"""
        You are a biomedical research AI specializing in ME/CFS.
        Review the following study summaries and propose 3 new causal hypotheses
        linking biological mechanisms and biomarkers.

        Each hypothesis must be valid JSON with:
          title (string),
          summary (string),
          confidence (float 0–1),
          mechanisms (array of strings),
          biomarkers (array of strings),
          citations (array of short references).

        Summaries:
        {text_corpus}
        """

        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a biomedical AI assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        raw = completion.choices[0].message.content.strip()
        try:
            ai_generated = json.loads(raw)
            if isinstance(ai_generated, dict) and "hypotheses" in ai_generated:
                ai_generated = ai_generated["hypotheses"]
        except Exception:
            ai_generated = []

        # ----------------------------------------------------------------
        # 4️⃣ Normalize + ensure fields + UUIDs
        # ----------------------------------------------------------------
        for h in ai_generated:
            h["id"] = str(uuid.uuid4())
            h["confidence"] = (
                float(h.get("confidence", 0.5))
                if isinstance(h.get("confidence"), (int, float))
                else 0.5
            )

        # ----------------------------------------------------------------
        # 5️⃣ Merge + semantic deduplication
        # ----------------------------------------------------------------
        combined = (seeded or []) + (ai_generated or [])
        unique = deduplicate_semantically(combined, threshold=0.85)

        return unique

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating hypotheses: {e}"
        )
