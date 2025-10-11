# main.py
from fastapi import FastAPI
from routes import papers

app = FastAPI(
    title="Open ME/CFS API",
    description="Public API serving summarized ME/CFS research data",
    version="0.1.0",
)

# Register paper routes
app.include_router(papers.router)


@app.get("/")
def root():
    """Root endpoint providing API info"""
    return {
        "project": "Open ME/CFS",
        "description": "AI-summarized ME/CFS research papers",
        "endpoints": ["/papers", "/paper/{pmid}", "/search?q=term", "/docs"],
    }
