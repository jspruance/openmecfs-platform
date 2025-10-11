# routes/semantic.py
from fastapi import APIRouter, Query, HTTPException
from openai import OpenAI
from utils.db import supabase
import os

router = APIRouter(prefix="/papers", tags=["semantic"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "text-embedding-3-small"


@router.get("/semantic")
def semantic_search(
    q: str = Query(..., description="Semantic search query"),
    limit: int = Query(5, ge=1, le=20),
):
    """Semantic similarity search using OpenAI embeddings + Supabase RPC"""
    try:
        _client = get_openai_client()

        # Create query embedding
        embedding = _client.embeddings.create(
            input=q, model=_MODEL
        ).data[0].embedding

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
