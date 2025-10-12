# routes/papers.py
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Paper
from typing import Optional

router = APIRouter(prefix="/papers", tags=["papers"])

# Dependency: open a DB session per request


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🧠 List Papers (filters, pagination, sorting)
@router.get("/")
def list_papers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("year", description="Sort by pmid, title, or year"),
    order: str = Query("desc", description="asc or desc"),
    author: Optional[str] = Query(
        None, description="Filter by author substring"),
    year: Optional[int] = Query(
        None, description="Filter by publication year"),
):
    query = db.query(Paper)

    if author:
        query = query.filter(Paper.authors.ilike(f"%{author}%"))
    if year:
        query = query.filter(Paper.year == year)

    sort_field = getattr(Paper, sort, Paper.year)
    query = query.order_by(
        sort_field.desc() if order.lower() == "desc" else sort_field.asc()
    )

    results = query.offset((page - 1) * limit).limit(limit).all()
    return results


# 🔍 Search Endpoint
@router.get("/search")
def search_papers(
    q: str = Query(..., description="Full-text search"),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    search = f"%{q.lower()}%"
    results = (
        db.query(Paper)
        .filter(
            (Paper.title.ilike(search))
            | (Paper.abstract.ilike(search))
            | (Paper.authors.ilike(search))
        )
        .limit(limit)
        .all()
    )
    return results


# 📄 Single Paper by PMID
@router.get("/{pmid}")
def get_paper(pmid: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.pmid == pmid).first()
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {pmid} not found")
    return paper
