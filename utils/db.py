# utils/db.py
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import lru_cache
from datetime import datetime
from cachetools import TTLCache, cached
import os

# ------------------------------------------------------------
# 🔐 Environment & Supabase Client
# ------------------------------------------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing Supabase credentials.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ------------------------------------------------------------
# ⚡ Cache Configuration
# ------------------------------------------------------------
# Short-term search cache: 30 sec TTL, 200 unique queries max
_search_cache = TTLCache(maxsize=200, ttl=30)


# ------------------------------------------------------------
# 📚 Paper Retrieval
# ------------------------------------------------------------
def get_papers(limit: int = 10, offset: int = 0, sort: str = "pmid", order: str = "asc"):
    """Fetch a paginated list of papers from Supabase"""
    query = supabase.table("papers").select(
        "*").range(offset, offset + limit - 1)
    query = query.order(sort, desc=(order == "desc"))
    return query.execute().data


def get_paper_by_pmid(pmid: str):
    """Fetch a single paper and its summaries"""
    paper = supabase.table("papers").select(
        "*").eq("pmid", pmid).execute().data
    if not paper:
        return None

    summaries = supabase.table("summaries").select(
        "*").eq("pmid", pmid).execute().data
    return {"paper": paper[0], "summaries": summaries[0] if summaries else None}


# ------------------------------------------------------------
# 🔍 Search (cached)
# ------------------------------------------------------------
@cached(_search_cache)
def search_papers(q=None, limit=10, author=None, year=None):
    """Simple full-text search over title, authors, and abstract"""
    papers = get_papers(limit=1000)

    if not q:
        return papers[:limit]

    q_lower = q.lower()
    results = []

    for p in papers:
        title = p.get("title", "").lower()
        authors = p.get("authors", [])
        abstract = p.get("abstract", "").lower()

        # normalize author list to string
        if isinstance(authors, list):
            authors_str = " ".join(authors).lower()
        else:
            authors_str = str(authors).lower()

        if (
            q_lower in title
            or q_lower in authors_str
            or q_lower in abstract
        ):
            results.append(p)

    # Apply optional filters
    if author:
        results = [
            p for p in results
            if author.lower() in " ".join(p.get("authors", [])).lower()
        ]

    if year:
        results = [p for p in results if str(p.get("year")) == str(year)]

    return results[:limit]


# ------------------------------------------------------------
# 📊 Stats + Analytics
# ------------------------------------------------------------
@lru_cache(maxsize=1)
def get_stats():
    """Aggregate counts and trends for /stats"""
    papers = supabase.table("papers").select("year, authors").execute().data
    if not papers:
        return {"message": "No papers found"}

    total_papers = len(papers)
    year_counts, author_counts = {}, {}

    for p in papers:
        # Year distribution
        year = p.get("year")
        if year:
            year_counts[year] = year_counts.get(year, 0) + 1

        # Author frequency
        authors = p.get("authors") or []
        if isinstance(authors, list):
            for a in authors:
                author_counts[a] = author_counts.get(a, 0) + 1

    top_authors = sorted(author_counts.items(),
                         key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_papers": total_papers,
        "year_distribution": year_counts,
        "top_authors": [{"name": a, "count": c} for a, c in top_authors],
        "updated": datetime.utcnow().isoformat(),
    }


# ------------------------------------------------------------
# 🧾 Metadata Endpoint Helper
# ------------------------------------------------------------
def get_metadata():
    """Return basic dataset metadata summary"""
    stats = get_stats()
    return {
        "source": "Supabase",
        "total_papers": stats.get("total_papers", 0),
        "last_updated": stats.get("updated"),
        "top_authors": stats.get("top_authors", []),
    }

# ------------------------------------------------------------
# 📦 Datasets (Placeholder)
# ------------------------------------------------------------


def get_datasets():
    """Return available datasets (placeholder until implemented)"""
    return [
        {
            "name": "mecfs_papers",
            "description": "Summarized ME/CFS research dataset",
            "source": "Supabase 'papers' table",
            "record_count": len(get_papers(limit=1000)),
            "last_updated": datetime.utcnow().isoformat(),
        }
    ]
