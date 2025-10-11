# utils/db.py
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing Supabase credentials.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ------------------------------------------------------------
# 🧠 Query Helpers
# ------------------------------------------------------------

def get_papers(limit: int = 10, offset: int = 0, sort: str = "pmid", order: str = "asc"):
    """Fetch a paginated list of papers"""
    query = supabase.table("papers").select(
        "*").range(offset, offset + limit - 1)
    query = query.order(sort, desc=(order == "desc"))
    return query.execute().data


def get_paper_by_pmid(pmid: str):
    """Fetch single paper with summaries joined"""
    paper = supabase.table("papers").select(
        "*").eq("pmid", pmid).execute().data
    if not paper:
        return None
    summaries = supabase.table("summaries").select(
        "*").eq("pmid", pmid).execute().data
    return {"paper": paper[0], "summaries": summaries[0] if summaries else None}


def search_papers(term: str, limit: int = 10, author: str | None = None, year: int | None = None):
    """
    Production-grade full-text search for Open ME/CFS.
    Searches title, abstract, and authors_text (flattened).
    """
    query = supabase.table("papers").select("*")

    # 🔍 Flexible full-text match
    if term:
        pattern = f"%{term}%"
        query = query.or_(
            f"title.ilike.{pattern},abstract.ilike.{pattern},authors_text.ilike.{pattern}")

    # 👤 Optional author filter
    if author:
        query = query.ilike("authors_text", f"%{author}%")

    # 📅 Optional year filter
    if year:
        query = query.eq("year", year)

    query = query.limit(limit)
    results = query.execute().data

    # 🧠 Simple ranking
    if results and term:
        results.sort(
            key=lambda p: (
                term.lower() in p.get("title", "").lower(),
                term.lower() in p.get("abstract", "").lower(),
                term.lower() in p.get("authors_text", "").lower(),
            ),
            reverse=True,
        )

    return results


def get_metadata():
    """Fetch latest dataset metadata"""
    result = (
        supabase.table("datasets")
        .select("*")
        .order("imported_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    if not result:
        return None
    return result[0]
