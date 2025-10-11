# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import papers

app = FastAPI(
    title="Open ME/CFS API",
    description="Public API serving summarized ME/CFS research data",
    version="0.1.1",
)

# ✅ Allow cross-origin requests (for your upcoming Next.js frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(papers.router)


@app.get("/")
def root():
    """Root endpoint providing API info"""
    return {
        "project": "Open ME/CFS",
        "description": "AI-summarized ME/CFS research papers",
        "version": "0.1.1",
        "endpoints": [
            "/papers",
            "/papers/{pmid}",
            "/papers/search?q=",
            "/papers/meta",
            "/health",
        ],
    }

# 🆕 simple health check


@app.get("/health")
def health_check():
    return {"status": "ok"}
