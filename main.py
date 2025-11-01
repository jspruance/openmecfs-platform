from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# Host validation support only (NO HTTPS redirect here)
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Routes
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
# 🌐 CORS (FIRST middleware, mandatory order)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://openmecfs.org",
        "https://www.openmecfs.org",
        "https://openmecfs-ui.vercel.app",
        "https://openmecfs-platform-production.up.railway.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# 🌐 Trusted hosts only (NO HTTPS redirect here; Railway handles TLS)
# ------------------------------------------------------------
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "openmecfs.org",
        "www.openmecfs.org",
        "*.vercel.app",
        "*.railway.app",
        "localhost",
        "127.0.0.1",
    ],
)

# ------------------------------------------------------------
# 🌐 Manual CORS preflight fallback (Railway sometimes drops OPTIONS)
# ------------------------------------------------------------


@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return Response(status_code=200)

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

# ✅ Support old `/papers-sb` path your frontend is calling
app.include_router(papers.router, prefix="/papers-sb")

# ------------------------------------------------------------
# 🔍 Root Route
# ------------------------------------------------------------


@app.get("/")
def root():
    return {
        "project": "Open ME/CFS",
        "description": "AI-summarized ME/CFS research data",
        "version": "0.1.2",
        "endpoints": [
            "/papers",
            "/papers-sb",
            "/papers/{pmid}",
            "/papers/search?q=",
            "/papers/meta",
            "/health",
            "/embeddings",
        ],
    }

# ------------------------------------------------------------
# ❤️ Health Check
# ------------------------------------------------------------


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ------------------------------------------------------------
# 🔥 Local only
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
