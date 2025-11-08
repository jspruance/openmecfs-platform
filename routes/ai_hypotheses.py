# routes/ai_hypotheses.py
from fastapi import APIRouter
from supabase import create_client
import os
from openai import OpenAI

router = APIRouter()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@router.get("/ai/hypotheses")
def get_ai_hypotheses():
    # 1️⃣ Fetch recent summarized papers + mechanisms
    summaries = client.table("paper_summaries").select("*").execute().data
    mechanisms = client.table("mechanism_graph").select("*").execute().data

    # 2️⃣ Build a compact prompt for GPT reasoning
    text_corpus = "\n".join(
        [f"- {s['one_sentence']}" for s in summaries[:40]]
    )

    prompt = f"""
    You are an expert biomedical AI. Analyze the following summaries of ME/CFS studies
    and propose 3 causal hypotheses linking key mechanisms and biomarkers.

    For each hypothesis, return a JSON object with:
    title, summary, confidence (0–1), mechanisms[], biomarkers[], citations[].

    Summaries:
    {text_corpus}
    """

    # 3️⃣ Generate using GPT
    completion = openai.responses.create(
        model="gpt-4.1",
        response_format={"type": "json"},
        input=prompt,
        max_output_tokens=600
    )

    try:
        hypotheses = completion.output_parsed
    except Exception:
        hypotheses = []

    return hypotheses
