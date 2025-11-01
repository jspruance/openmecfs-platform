app = FastAPI(...)

# ✅ Trust proxy headers / enforce HTTPS
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(HTTPSRedirectMiddleware)
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

# ✅ CORS
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
