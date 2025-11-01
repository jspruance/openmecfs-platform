# routes/clusters.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from utils.db import supabase  # adjust if your supabase client lives elsewhere

router = APIRouter(prefix="/clusters", tags=["Clusters"])


def _fetch_clusters() -> List[Dict[str, Any]]:
    """
    Fetch cluster metadata from your backing store.
    Adjust the table/columns as needed to match your schema.
    """
    try:
        # Example: table 'subtype_clusters' with these columns
        resp = (
            supabase
            .table("subtype_clusters")
            .select("cluster_num, cluster_label, keywords, cluster_summary")
            .order("cluster_num")
            .execute()
        )
        return resp.data or []
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching clusters: {e}")

# ✅ Accepts /clusters  (no trailing slash)


@router.get("")
def get_clusters_no_slash():
    return _fetch_clusters()

# ✅ Accepts /clusters/ (trailing slash)


@router.get("/")
def get_clusters_with_slash():
    return _fetch_clusters()
