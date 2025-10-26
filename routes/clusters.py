# routes/clusters.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from utils.db import supabase

router = APIRouter(prefix="/clusters", tags=["Clusters"])

# ------------------------------------------------------------
# 🧩 Data Models
# ------------------------------------------------------------


class Cluster(BaseModel):
    id: str
    cluster_num: Optional[int]
    cluster_label: Optional[str]
    keywords: Optional[List[str]]
    cluster_summary: Optional[str]


# ------------------------------------------------------------
# 🚀 Routes
# ------------------------------------------------------------
@router.get("/", response_model=List[Cluster])
def get_clusters():
    """Return all cluster metadata (label, keywords, summary)"""
    try:
        result = supabase.table("subtype_clusters").select("*").execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="No clusters found")
        return result.data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching clusters: {str(e)}")


@router.get("/{cluster_num}", response_model=Cluster)
def get_cluster_by_num(cluster_num: int):
    """Return a single cluster by numeric ID"""
    try:
        result = (
            supabase.table("subtype_clusters")
            .select("*")
            .eq("cluster_num", cluster_num)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=404, detail=f"Cluster {cluster_num} not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching cluster: {str(e)}")
