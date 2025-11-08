from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from openai import OpenAI
import os
import uuid
import numpy as np
from numpy.linalg import norm
import datetime
import json
import re

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
    if norm(a) == 0 or norm(b) == 0:
        return 0
    return float(np.dot(a, b) / (norm(a) * norm(b)))


# --------------------------------------------------------------------
# 🚀 Helper: normalize title
# --------------------------------------------------------------------
def normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


# --------------------------------------------------------------------
# 🚀 Combined Hypotheses Endpoint (Non-destructive sync + timestamp)
# --------------------------------------------------------------------
@router.get("/hypotheses")
async def get_ai_hypotheses():
    """
    Returns both:
      1. Existing hypotheses stored in Supabase (ai_hypotheses table)
      2. New AI-generated hypotheses from paper_summaries
         — with semantic + textual deduplication
         — and non-destructive Supabase sync
         — includes last_synced_at timestamp for each hypothesis
    """

    try:
        print("DEBUG: /ai/hypotheses endpoint hit ✅")

        # 1️⃣ Pull existing hypotheses
        existing = (
            supabase.table("ai_hypotheses")
            .select("*")
            .order("created_at", desc=True)
            .execute()
            .data
        ) or []
        print(f"DEBUG: Retrieved {len(existing)} existing hypotheses.")

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
            return existing

        text_corpus = "\n".join(f"- {s['one_sentence']}" for s in summaries)

        # ----------------------------------------------------------------
        # 3️⃣ Generate fresh hypotheses via GPT
        # ----------------------------------------------------------------
        prompt = f"""
        You are a biomedical research AI specializing in ME/CFS.
        Review the following study summaries and propose 3 new causal hypotheses
        linking biological mechanisms and biomarkers.

        Each hypothesis must be returned as a JSON array of objects with:
          title (string),
          summary (string),
          confidence (float 0–1),
          mechanisms (array of strings),
          biomarkers (array of strings),
          citations (array of short references).

        Summaries:
        {text_corpus}
        """

        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a biomedical AI researcher."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )

            content = completion.choices[0].message.content.strip()
            ai_generated = json.loads(content)
            print(f"DEBUG: GPT returned {len(ai_generated)} raw hypotheses.")

        except json.JSONDecodeError:
            print("WARNING: GPT output was not valid JSON — skipping parse.")
            ai_generated = []
        except Exception as e:
            print(f"ERROR: GPT generation failed: {e}")
            ai_generated = []

        # ----------------------------------------------------------------
        # 4️⃣ Normalize + assign metadata
        # ----------------------------------------------------------------
        now = datetime.datetime.utcnow().isoformat()
        for h in ai_generated:
            h["id"] = str(uuid.uuid4())
            conf = h.get("confidence", 0.5)
            if not isinstance(conf, (int, float)):
                conf = 0.5
            h["confidence"] = max(0, min(1, conf))
            h["created_at"] = now
            h["last_synced_at"] = now

        combined = existing + ai_generated
        print(f"DEBUG: Total before dedup: {len(combined)}")

        # ----------------------------------------------------------------
        # 5️⃣ Lightweight title prefilter
        # ----------------------------------------------------------------
        seen_titles = set()
        filtered = []
        for h in combined:
            title_key = normalize_title(h.get("title", ""))
            if any(
                title_key in t or t in title_key
                for t in seen_titles
                if len(title_key) > 10
            ):
                continue
            seen_titles.add(title_key)
            filtered.append(h)

        print(f"DEBUG: After title prefilter: {len(filtered)} remain.")

        # ----------------------------------------------------------------
        # 6️⃣ Compute embeddings via OpenAI
        # ----------------------------------------------------------------
        titles = [h["title"] for h in filtered if "title" in h]
        if not titles:
            return filtered

        embedding_response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=titles,
        )

        embeddings = [d.embedding for d in embedding_response.data]

        # ----------------------------------------------------------------
        # 7️⃣ Semantic deduplication (threshold = 0.88)
        # ----------------------------------------------------------------
        unique = []
        seen = []

        for i, emb in enumerate(embeddings):
            if not isinstance(emb, (list, np.ndarray)) or len(emb) == 0:
                continue

            duplicate = False
            for seen_emb in seen:
                try:
                    if cosine_sim(emb, seen_emb) >= 0.88:
                        duplicate = True
                        break
                except Exception:
                    continue

            if not duplicate:
                unique.append(filtered[i])
                seen.append(emb)

        print(
            f"DEBUG: Deduped to {len(unique)} unique hypotheses (threshold=0.88).")

        # ----------------------------------------------------------------
        # 8️⃣ Supabase sync — Non-destructive append + last_synced_at
        # ----------------------------------------------------------------
        try:
            print("DEBUG: Syncing deduped hypotheses to Supabase...")

            existing_titles = {normalize_title(
                h["title"]) for h in existing if "title" in h}
            new_unique = [
                {**h, "last_synced_at": now}
                for h in unique
                if normalize_title(h["title"]) not in existing_titles
            ]

            if new_unique:
                supabase.table("ai_hypotheses").insert(new_unique).execute()
                print(f"DEBUG: Inserted {len(new_unique)} new hypotheses.")
            else:
                print("DEBUG: No new unique hypotheses to insert.")

        except Exception as sync_err:
            print(f"WARNING: Could not sync new hypotheses: {sync_err}")

        return unique

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating hypotheses: {e}")
