# utils/generate_embeddings.py
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
import os
from tqdm import tqdm
import time

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "text-embedding-3-small"


def generate_embeddings():
    # Fetch papers without embeddings
    papers = (
        supabase.table("papers")
        .select("pmid, title, abstract")
        .is_("embedding", None)
        .limit(50)  # run in batches
        .execute()
        .data
    )

    if not papers:
        print("✅ All papers already have embeddings.")
        return

    print(f"🧠 Found {len(papers)} papers needing embeddings...")

    for p in tqdm(papers, desc="Embedding papers"):
        try:
            text = f"{p['title']} {p['abstract'] or ''}"
            embedding = client.embeddings.create(
                model=MODEL, input=text
            ).data[0].embedding

            supabase.table("papers").update(
                {"embedding": embedding}
            ).eq("pmid", p["pmid"]).execute()

            time.sleep(0.2)  # avoid rate limits
        except Exception as e:
            print(f"❌ Error embedding {p['pmid']}: {e}")

    print("✅ Embedding batch complete.")


if __name__ == "__main__":
    generate_embeddings()
