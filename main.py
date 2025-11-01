from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Existing route modules
from routes import papers, datasets, stats, cache, semantic, clusters, papers_supabase

# ✅ Embeddings route
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
# 🌐 Reverse Proxy & Host Security (Railway + Vercel)
# ------------------------------------------------------------

# ✅ Trust X-Forwarded-* headers (Railway/Vercel proxy)
app.add_middleware(ProxyHeadersMiddleware)

# ✅ Restrict hosts (prevents HTTP downgrade issues)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "openmecfs-platform-production.up.railway.app",
        "openmecfs.org",
        "*.railway.app",
        "localhost",
        "127.0.0.1",
    ],
)

# ------------------------------------------------------------
# 🌐 CORS Configuration
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://openmecfs.org",
        "https://www.openmecfs.org",
        "https://openmecfs-ui.vercel.app",
        "https://openmecfs-platform-production.up.railway.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
app.include_router(embeddings_router)

# ------------------------------------------------------------
# 🔍 Root Endpoint
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
# ❤️ Health Check
# ------------------------------------------------------------


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ------------------------------------------------------------
# 🚀 Run app (Railway needs this)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
