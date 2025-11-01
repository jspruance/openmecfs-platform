from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Existing route modules
from routes import papers, datasets, stats, cache, semantic, clusters, papers_supabase
from routes.embeddings import router as embeddings_router

# ------------------------------------------------------------
# 🚀 App Configuration
# ------------------------------------------------------------
app = FastAPI(
    title="Open ME/CFS API",
    description="Public API serving summarized ME/CFS research data",
    version="0.1.2",
)

# ------------------------------------------------------------
# 🌐 Force HTTPS (fix mixed-content)
# ------------------------------------------------------------


@app.middleware("http")
async def redirect_http_to_https(request: Request, call_next):
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(str(url))
    return await call_next(request)

# ------------------------------------------------------------
# 🌐 CORS (Frontend allowed)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://openmecfs.org",
        "https://www.openmecfs.org",
        "https://openmecfs-ui.vercel.app",
        "https://openmecfs-platform-production.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# 📚 Routes
# ------------------------------------------------------------
app.include_router(papers.router)
app.include_router(datasets.router)
app.include_router(stats.router)
app.include_router(cache.router)
app.include_router(semantic.router)
app.include_router(clusters.router)
app.include_router(papers_supabase.router)
app.include_router(embeddings_router)

# ------------------------------------------------------------
# 🔍 Root
# ------------------------------------------------------------


@app.get("/")
def root():
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
            "/embeddings",
        ],
    }

# ------------------------------------------------------------
# ❤️ Health
# ------------------------------------------------------------


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ------------------------------------------------------------
# 🚀 Run (Railway)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
