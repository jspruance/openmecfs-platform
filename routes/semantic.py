# routes/semantic.py
from fastapi import APIRouter, HTTPException, Query
from utils.db import supabase
from openai import OpenAI
import os

router = APIRouter(prefix="/semantic", tags=["semantic"])

_MODEL = "text-embedding-3-small"


def get_openai_client():
    """Return a configured OpenAI client or None if key missing."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ Warning: OPENAI_API_KEY not set. Semantic routes disabled.")
        return None
    return OpenAI(api_key=api_key)


@router.get("/")
def semantic_search(
    q: str = Query(..., description="Semantic search query"),
    limit: int = Query(5, ge=1, le=50),
):
    """Semantic similarity search using OpenAI embeddings + Supabase RPC"""

    _client = get_openai_client()
    if not _client:
        return {"message": "Semantic search unavailable in this environment."}

    try:
        embedding = _client.embeddings.create(
            input=q, model=_MODEL).data[0].embedding
        res = supabase.rpc(
            "match_papers", {
                "query_embedding": embedding, "match_count": limit}
        ).execute()

        return {
            "query": q,
            "count": len(res.data or []),
            "results": res.data or [],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
