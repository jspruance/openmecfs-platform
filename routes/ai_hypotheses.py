# routes/ai_hypotheses.py
from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from openai import OpenAI
import os
import uuid

# --------------------------------------------------------------------
# 🧠 Initialization
# --------------------------------------------------------------------
router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)


# --------------------------------------------------------------------
# 🚀 Combined Hypotheses Endpoint
# --------------------------------------------------------------------
# ✅ Correct path (prefix /ai will be added in main.py)
@router.get("/hypotheses")
async def get_ai_hypotheses():
    """
    Returns both:
      1. Seeded hypotheses stored in Supabase (ai_hypotheses table)
      2. Live AI-generated hypotheses derived from paper_summaries
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
        # 2️⃣ Gather recent paper summaries to ground AI reasoning
        # ----------------------------------------------------------------
        summaries = (
            supabase.table("paper_summaries")
            .select("one_sentence")
            .limit(40)
            .execute()
            .data
        )
        if not summaries:
            return seeded or []

        text_corpus = "\n".join(f"- {s['one_sentence']}" for s in summaries)

        # ----------------------------------------------------------------
        # 3️⃣ Prompt GPT for fresh causal hypotheses
        # ----------------------------------------------------------------
        prompt = f"""
        You are a biomedical research AI specializing in ME/CFS.
        Review the following study summaries and propose 3 new causal hypotheses
        linking biological mechanisms and biomarkers.

        Each hypothesis must be a valid JSON object with:
          title (string),
          summary (string),
          confidence (float 0–1),
          mechanisms (array of strings),
          biomarkers (array of strings),
          citations (array of short references).

        Summaries:
        {text_corpus}
        """

        completion = openai.responses.create(
            model="gpt-4.1",
            input=prompt,
            response_format={"type": "json"},
            max_output_tokens=800,
        )

        try:
            ai_generated = completion.output_parsed
        except Exception:
            ai_generated = []

        # ----------------------------------------------------------------
        # 4️⃣ Normalize data and attach UUIDs
        # ----------------------------------------------------------------
        for h in ai_generated:
            h["id"] = str(uuid.uuid4())
            if "confidence" in h and isinstance(h["confidence"], (int, float)):
                h["confidence"] = max(0, min(1, h["confidence"]))
            else:
                h["confidence"] = 0.5

        # ----------------------------------------------------------------
        # 5️⃣ Merge both datasets (seeded + AI)
        # ----------------------------------------------------------------
        combined = (seeded or []) + (ai_generated or [])
        return combined

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating hypotheses: {e}")
