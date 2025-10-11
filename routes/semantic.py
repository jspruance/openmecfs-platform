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
    limit: int = Query(5, ge=1, le=20)
):
    """Return semantically similar papers using vector similarity"""
    # 1️⃣ Generate embedding for the search query
    try:
        query_embedding = client.embeddings.create(
            input=q, model=MODEL
        ).data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")

    # 2️⃣ Query Supabase (pgvector similarity search)
    try:
        response = supabase.rpc(
            "match_papers",
            {"query_embedding": query_embedding, "match_count": limit}
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase RPC error: {e}")

    if not response.data:
        return {"query": q, "results": []}

    return {
        "query": q,
        "count": len(response.data),
        "results": response.data
    }
