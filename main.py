# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import papers, datasets, stats, cache, semantic, clusters, papers_supabase

# ------------------------------------------------------------
# 🚀 App Configuration
# ------------------------------------------------------------
app = FastAPI(
    title="Open ME/CFS API",
    description="Public API serving summarized ME/CFS research data",
    version="0.1.2",
)

# ------------------------------------------------------------
# 🌐 CORS Configuration (Frontend Access)
# ------------------------------------------------------------
# Allow all origins during development.
# Later, replace "*" with your deployed frontend URL:
# e.g., ["https://openmecfs-ui.vercel.app"]
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# 📚 Route Registration
# ------------------------------------------------------------
app.include_router(papers.router)
app.include_router(datasets.router)
app.include_router(stats.router)
app.include_router(cache.router)
app.include_router(semantic.router)
app.include_router(clusters.router)
app.include_router(papers_supabase.router)

# ------------------------------------------------------------
# 🔍 Root Endpoint
# ------------------------------------------------------------


@app.get("/")
def root():
    """Root endpoint providing API info"""
    return {
        "project": "Open ME/CFS",
        "description": "AI-summarized ME/CFS research papers",
        "version": "0.1.2",
        "endpoints": [
            "/papers",
            "/papers/{pmid}",
            "/papers/search?q=",
            "/papers/meta",
            "/health",
        ],
    }

# ------------------------------------------------------------
# ❤️ Health Check
# ------------------------------------------------------------


@app.get("/health")
def health_check():
    """Simple uptime check"""
    return {"status": "ok"}
