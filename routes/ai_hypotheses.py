from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from openai import OpenAI
import os
import uuid
import numpy as np
from numpy.linalg import norm
import datetime

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
# 🚀 Helper: cosine similarity
# --------------------------------------------------------------------


def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (norm(a) * norm(b)))

# --------------------------------------------------------------------
# 🚀 Combined Hypotheses Endpoint (with OpenAI-based dedup + Supabase sync)
# --------------------------------------------------------------------


@router.get("/hypotheses")
async def get_ai_hypotheses():
    """
    Returns both:
      1. Seeded hypotheses stored in Supabase (ai_hypotheses table)
      2. Live AI-generated hypotheses derived from paper_summaries
         — with semantic deduplication using OpenAI embeddings
         — and automatic Supabase upsert (keeps table clean)
    """

    try:
        print("DEBUG: /ai/hypotheses endpoint hit ✅")

        # 1️⃣ Pull existing hypotheses
        seeded = (
            supabase.table("ai_hypotheses")
            .select("*")
            .order("created_at", desc=True)
            .execute()
            .data
        ) or []
        print(f"DEBUG: Retrieved {len(seeded)} seeded hypotheses.")

        # 2️⃣ Gather paper summaries
        summaries = (
            supabase.table("paper_summaries")
            .select("one_sentence")
            .limit(40)
            .execute()
            .data
        ) or []
        print(f"DEBUG: Retrieved {len(summaries)} paper summaries.")

        if not summaries:
            return seeded

        text_corpus = "\n".join(f"- {s['one_sentence']}" for s in summaries)

        # 3️⃣ Generate fresh hypotheses via GPT
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
        except Exception as e:
            print(f"ERROR: Failed to parse GPT output: {e}")
            ai_generated = []

        # 4️⃣ Normalize + assign UUIDs
        for h in ai_generated:
            h["id"] = str(uuid.uuid4())
            conf = h.get("confidence", 0.5)
            if not isinstance(conf, (int, float)):
                conf = 0.5
            h["confidence"] = max(0, min(1, conf))
            h["created_at"] = datetime.datetime.utcnow().isoformat()

        all_hypotheses = seeded + ai_generated
        print(f"DEBUG: Total before dedup: {len(all_hypotheses)}")

        # 5️⃣ Compute embeddings via OpenAI
        titles = [h["title"] for h in all_hypotheses if "title" in h]
        if not titles:
            return all_hypotheses

        embedding_response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=titles,
        )

        embeddings = [d.embedding for d in embedding_response.data]

        # 6️⃣ Deduplicate (cosine similarity threshold)
        unique = []
        seen = []
        for i, emb in enumerate(embeddings):
            duplicate = False
            for seen_emb in seen:
                if cosine_sim(emb, seen_emb) >= 0.85:
                    duplicate = True
                    break
            if not duplicate:
                unique.append(all_hypotheses[i])
                seen.append(emb)

        print(f"DEBUG: Deduped to {len(unique)} unique hypotheses.")

        # 7️⃣ Supabase sync — overwrite ai_hypotheses table
        try:
            print("DEBUG: Syncing deduped hypotheses to Supabase...")
            # Clear old rows (optional: comment this out if you prefer append-only)
            supabase.table("ai_hypotheses").delete().neq(
                "id", "00000000-0000-0000-0000-000000000000").execute()

            # Bulk insert new clean set
            if unique:
                supabase.table("ai_hypotheses").insert(unique).execute()
            print("DEBUG: Supabase sync complete ✅")

        except Exception as sync_err:
            print(f"WARNING: Could not sync deduped hypotheses: {sync_err}")

        return unique

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating hypotheses: {e}")
