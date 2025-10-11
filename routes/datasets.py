from fastapi import APIRouter
from utils.db import get_datasets

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/")
def list_datasets():
    """Return all imported dataset versions"""
    datasets = get_datasets()
    return {"count": len(datasets), "datasets": datasets}
