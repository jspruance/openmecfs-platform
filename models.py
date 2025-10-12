# models.py
from sqlalchemy import Column, Integer, String, Text, ARRAY, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class Paper(Base):
    __tablename__ = "papers"

    pmid = Column(String, primary_key=True, index=True)
    title = Column(Text)
    abstract = Column(Text)
    authors = Column(ARRAY(String))
    year = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True))
    authors_text = Column(Text)
    embedding = Column(JSONB)  # or change to ARRAY(Float) if vector type
