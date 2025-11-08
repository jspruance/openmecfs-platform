# routes/ai_hypotheses.py
from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from openai import OpenAI
import os
import uuid
import json
import traceback

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)


@router.get("/hypotheses")
async def get_ai_hypotheses():
    try:
        print("🧠 /ai/hypotheses endpoint hit")

        seeded = (
            supabase.table("ai_hypotheses")
            .select("*")
            .order("created_at", desc=True)
            .execute()
            .data
        ) or []
        print(f"Retrieved {len(seeded)} seeded hypotheses.")

        summaries = (
            supabase.table("paper_summaries")
            .select("one_sentence")
            .limit(40)
            .execute()
            .data
        ) or []
        if not summaries:
            print("⚠️ No summaries found.")
            return seeded

        text_corpus = "\n".join(f"- {s['one_sentence']}" for s in summaries)

        prompt = f"""
        You are a biomedical research AI specializing in ME/CFS.
        Review the following study summaries and propose 3 new causal hypotheses
        linking biological mechanisms and biomarkers.

        Each hypothesis must be valid JSON with:
        title, summary, confidence (0–1),
        mechanisms[], biomarkers[], citations[].

        Return a JSON array (not text).
        Summaries:
        {text_corpus}
        """

        print("Sending prompt to OpenAI...")
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = completion.choices[0].message.content.strip()

        ai_generated = []
        try:
            ai_generated = json.loads(
                content[content.find("["):content.rfind("]")+1])
        except Exception as e:
            print("⚠️ Parsing error:", e)
            ai_generated = []

        saved_titles = {h["title"].lower().strip()
                        for h in seeded if h.get("title")}
        new_hypotheses = []

        for h in ai_generated:
            title = h.get("title", "").strip()
            if not title or title.lower() in saved_titles:
                continue

            new_hypotheses.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "summary": h.get("summary", ""),
                "confidence": float(h.get("confidence", 0.5)),
                "mechanisms": h.get("mechanisms", []),
                "biomarkers": h.get("biomarkers", []),
                "citations": h.get("citations", []),
                "source": "AI"
            })

        print(f"💾 {len(new_hypotheses)} new hypotheses ready for insert.")

        if new_hypotheses:
            try:
                res = supabase.table("ai_hypotheses").insert(
                    new_hypotheses).execute()
                print("✅ Supabase insert result:", res)
            except Exception as e:
                print("❌ Supabase insert failed:", str(e))

        combined = new_hypotheses + seeded
        print(f"Returning {len(combined)} total hypotheses.")
        return combined

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
