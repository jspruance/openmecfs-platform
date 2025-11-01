from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# HTTPS + proxy support
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

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
# 🌐 Trust Railway Proxy & Force HTTPS
# ------------------------------------------------------------
# respect X-Forwarded-* headers from Railway
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# force HTTPS for any accidental HTTP traffic
app.add_middleware(HTTPSRedirectMiddleware)

# verify incoming hosts
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
# 🌐 CORS
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
# 🔍 Root Route
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
# 🔥 Uvicorn (local only — Railway ignores this)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
