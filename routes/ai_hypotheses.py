# routes/ai_hypotheses.py
from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from openai import OpenAI
import os

router = APIRouter()

# Supabase + OpenAI setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)


@router.get("/ai/hypotheses")
async def get_ai_hypotheses():
    try:
        # 1️⃣ Pull existing hypotheses (seeded or saved)
        seeded = (
            supabase.table("ai_hypotheses")
            .select("*")
            .order("created_at", desc=True)
            .execute()
            .data
        )

        # 2️⃣ Fetch recent paper summaries and mechanisms
        summaries = supabase.table("paper_summaries").select(
            "one_sentence").limit(40).execute().data
        if not summaries:
            return seeded or []

        text_corpus = "\n".join(
            [f"- {s['one_sentence']}" for s in summaries]
        )

        # 3️⃣ Ask GPT to propose new hypotheses
        prompt = f"""
        You are an expert biomedical AI analyzing ME/CFS research.
        Based on the following study summaries, propose 3 causal hypotheses
        connecting mechanisms and biomarkers.

        Return JSON with:
        title, summary, confidence (0–1), mechanisms[], biomarkers[], citations[].

        Summaries:
        {text_corpus}
        """

        completion = openai.responses.create(
            model="gpt-4.1",
            response_format={"type": "json"},
            input=prompt,
            max_output_tokens=800,
        )

        try:
            ai_generated = completion.output_parsed
        except Exception:
            ai_generated = []

        # 4️⃣ Merge both datasets
        combined = (seeded or []) + (ai_generated or [])
        return combined

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
