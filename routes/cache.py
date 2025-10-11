# routes/cache.py
import os
from fastapi import APIRouter, HTTPException, Header
from utils.db import _search_cache

router = APIRouter(prefix="/cache", tags=["cache"])

# Optional admin token (only enforced in production)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")


@router.get("/status")
def cache_status():
    """Returns current search cache stats"""
    return {
        "search_cache_items": len(_search_cache),
        "cache_ttl_seconds": _search_cache.ttl,
        "maxsize": _search_cache.maxsize,
    }


@router.post("/clear")
def clear_cache(x_admin_token: str | None = Header(None)):
    """
    Clears all cached search results.
    Requires X-Admin-Token header if ADMIN_TOKEN is set in environment.
    """
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=403, detail="Forbidden: invalid admin token.")

    _search_cache.clear()
    return {"message": "✅ Search cache cleared successfully."}
