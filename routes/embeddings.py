from fastapi import APIRouter
from supabase import create_client
import os

router = APIRouter()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


@router.get("/embeddings")
def get_embeddings():
    result = supabase.table("papers").select(
        "pmid, cluster, umap_x, umap_y"
    ).execute()

    rows = result.data or []

    return [
        {
            "id": r["pmid"],
            "cluster_label": r["cluster"],
            "x": r["umap_x"],
            "y": r["umap_y"],
        }
        for r in rows
        if r.get("umap_x") is not None and r.get("umap_y") is not None
    ]
