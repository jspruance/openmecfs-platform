from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from openai import OpenAI
import os
import uuid
import json
import traceback

# --------------------------------------------------------------------
# 🧠 Initialization
# --------------------------------------------------------------------
router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Missing Supabase environment variables.")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ Missing OpenAI API key.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)

# --------------------------------------------------------------------
# 🚀 Combined + Persistent Hypotheses Endpoint
# --------------------------------------------------------------------


@router.get("/hypotheses")
async def get_ai_hypotheses():
    """
    Returns both:
      1️⃣ Seeded hypotheses stored in Supabase (ai_hypotheses table)
      2️⃣ Live AI-generated hypotheses (auto-saved with source='AI')
    """
    try:
        print("DEBUG: /ai/hypotheses endpoint hit ✅")

        # ----------------------------------------------------------------
        # 1️⃣ Retrieve seeded hypotheses
        # ----------------------------------------------------------------
        seeded = (
            supabase.table("ai_hypotheses")
            .select("*")
            .order("created_at", desc=True)
            .execute()
            .data
        ) or []
        print(f"DEBUG: Retrieved {len(seeded)} existing hypotheses.")

        # ----------------------------------------------------------------
        # 2️⃣ Gather paper summaries
        # ----------------------------------------------------------------
        summaries = (
            supabase.table("paper_summaries")
            .select("one_sentence")
            .limit(40)
            .execute()
            .data
        ) or []
        print(f"DEBUG: Retrieved {len(summaries)} paper summaries.")

        if not summaries:
            print("⚠️ No paper summaries found — returning seeded only.")
            return seeded

        text_corpus = "\n".join(f"- {s['one_sentence']}" for s in summaries)

        # ----------------------------------------------------------------
        # 3️⃣ Ask GPT for new causal hypotheses
        # ----------------------------------------------------------------
        prompt = f"""
        You are a biomedical research AI specializing in ME/CFS.
        Review the following study summaries and propose 3 new causal hypotheses
        linking biological mechanisms and biomarkers.

        Each hypothesis must be valid JSON with fields:
        - title (string)
        - summary (string)
        - confidence (float 0–1)
        - mechanisms (array of strings)
        - biomarkers (array of strings)
        - citations (array of short strings)

        Return a JSON array (not text).

        Summaries:
        {text_corpus}
        """

        print("DEBUG: Sending prompt to OpenAI...")

        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        content = completion.choices[0].message.content.strip()
        print("DEBUG: Raw OpenAI output (first 200 chars):", content[:200])

        ai_generated = []
        try:
            if content.startswith("{"):
                ai_generated = [json.loads(content)]
            elif content.startswith("["):
                ai_generated = json.loads(content)
            else:
                start = content.find("[")
                end = content.rfind("]")
                if start != -1 and end != -1:
                    ai_generated = json.loads(content[start:end+1])
        except Exception as e:
            print("ERROR parsing AI JSON:", e)
            ai_generated = []

        # ----------------------------------------------------------------
        # 4️⃣ Normalize, tag, and de-duplicate
        # ----------------------------------------------------------------
        saved_titles = {h["title"].strip().lower()
                        for h in seeded if h.get("title")}
        new_hypotheses = []

        for h in ai_generated:
            title = h.get("title", "").strip()
            if not title or title.lower() in saved_titles:
                continue

            new_hypotheses.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "summary": h.get("summary", ""),
                    "confidence": float(h.get("confidence", 0.5)),
                    "mechanisms": h.get("mechanisms", []),
                    "biomarkers": h.get("biomarkers", []),
                    "citations": h.get("citations", []),
                    "source": "AI",
                }
            )

        print(
            f"DEBUG: {len(new_hypotheses)} new unique AI hypotheses ready to save.")

        # ----------------------------------------------------------------
        # 5️⃣ Persist new AI-generated hypotheses
        # ----------------------------------------------------------------
        if new_hypotheses:
            try:
                supabase.table("ai_hypotheses").insert(
                    new_hypotheses).execute()
                print(
                    f"✅ Saved {len(new_hypotheses)} AI hypotheses to Supabase.")
            except Exception as e:
                print("⚠️ Failed to insert into Supabase:", str(e))

        # ----------------------------------------------------------------
        # 6️⃣ Return combined dataset
        # ----------------------------------------------------------------
        combined = new_hypotheses + seeded
        print(f"DEBUG: Returning {len(combined)} total hypotheses.")
        return combined

    except Exception as e:
        print("\n" + "=" * 80)
        print("🔥 ERROR in /ai/hypotheses:")
        print(traceback.format_exc())
        print("=" * 80 + "\n")
        raise HTTPException(
            status_code=500, detail=f"Error generating hypotheses: {e}")
