"""
Open ME/CFS — JSON → Supabase Importer
--------------------------------------
Reads summarized ME/CFS papers from JSON and loads them into Supabase.
"""

import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from utils.db import _search_cache

# Load credentials from .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing Supabase credentials. Check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Path to your summarized file
INPUT_PATH = "data/mecfs_papers_summarized_2025-10-11.json"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

papers = data["papers"] if "papers" in data else data
paper_count = len(papers)

print(f"📚 Importing {paper_count} papers to Supabase...")

# Track dataset import
dataset_info = {
    "file_name": os.path.basename(INPUT_PATH),
    "paper_count": paper_count,
    "model_info": {
        "technical_model": "philschmid/bart-large-cnn-samsum",
        "patient_model": "facebook/bart-large-cnn"
    }
}

supabase.table("datasets").insert(dataset_info).execute()

# Insert paper + summary records
for p in papers:
    try:
        # Papers table
        paper_entry = {
            "pmid": p.get("pmid"),
            "title": p.get("title"),
            "abstract": p.get("abstract"),
            "authors": p.get("authors"),
            "year": int(p.get("year")) if p.get("year") else None
        }
        supabase.table("papers").upsert(paper_entry).execute()

        # Summaries table
        summary_entry = {
            "pmid": p.get("pmid"),
            "technical_summary": p.get("technical_summary"),
            "patient_summary": p.get("patient_summary"),
            "technical_model": p.get("metadata", {}).get("technical_summary_model"),
            "patient_model": p.get("metadata", {}).get("patient_summary_model"),
            "summarized_at": p.get("metadata", {}).get("summarized_at")
        }
        supabase.table("summaries").upsert(summary_entry).execute()

    except Exception as e:
        print(f"❌ Error importing PMID {p.get('pmid')}: {e}")

# After successful import
_search_cache.clear()
print("🧹 Cache cleared after import.")
print("✅ Import complete.")
