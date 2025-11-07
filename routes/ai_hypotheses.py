from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os

router = APIRouter()

# Initialize Supabase client (requires env vars)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@router.get("/ai/hypotheses")
async def get_ai_hypotheses():
    try:
        response = supabase.table("ai_hypotheses").select("*").execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
