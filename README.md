# 🌍 Open ME/CFS API (AI Cure Platform)

**Open ME/CFS** is an open-source initiative combining **AI, open data, and community collaboration** to accelerate research and awareness around **Myalgic Encephalomyelitis / Chronic Fatigue Syndrome (ME/CFS)**.

This repository hosts the **FastAPI backend** powering the Open ME/CFS platform — serving AI-summarized, vector-searchable research papers and biological subtype metadata through Supabase.

---

## 🧠 Mission

> Democratize ME/CFS research by connecting patients, advocates, and researchers through open science and accessible data.

The API allows anyone to **search**, **filter**, and **analyze** ME/CFS research using both traditional keywords and AI-powered semantic search — no local model setup required.

---

## ⚙️ Tech Stack

| Layer               | Tools / Frameworks                   | Purpose                                 |
| ------------------- | ------------------------------------ | --------------------------------------- |
| **Backend**         | FastAPI + Uvicorn                    | REST API server                         |
| **Database**        | Supabase (PostgreSQL + pgvector)     | Storage of papers, embeddings, clusters |
| **AI Summaries**    | Hugging Face Transformers (BART, T5) | Technical + patient-friendly summaries  |
| **Semantic Search** | OpenAI Embeddings API                | Vector similarity & hybrid ranking      |
| **Clustering**      | UMAP + HDBSCAN + GPT Labeling        | AI Cure biological subtype engine       |
| **Caching / Stats** | Cachetools TTLCache                  | Lightweight in-memory cache             |
| **Frontend (Next)** | Next.js / React                      | Research Explorer UI (Phase 4C)         |

---

## 🧩 Folder Structure

```
openmecfs-platform/
│
├── main.py                        # FastAPI entry point + routers
├── routes/
│   ├── papers.py                  # SQLAlchemy-based legacy paper API
│   ├── papers_supabase.py         # Supabase-powered paper endpoint (/papers-sb)
│   ├── clusters.py                # Biological subtype metadata (/clusters)
│   ├── stats.py                   # Dataset stats
│   ├── cache.py                   # Cache control
│   └── semantic.py                # Semantic + hybrid search (WIP)
│
├── utils/
│   ├── db.py                      # Supabase client + helper functions
│   └── cache.py                   # In-memory TTL cache
│
├── database.py                    # SQLAlchemy engine for optional local use
├── tests/                         # Pytest regression tests
├── .env                           # Environment secrets
└── requirements.txt               # Dependencies
```

---

## 🚀 Getting Started

### 1️⃣ Create environment

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

If missing, reinstall base stack:

```bash
pip install "fastapi>=0.115,<0.116" "uvicorn[standard]>=0.30,<0.31"     "supabase>=2.3,<3.0" "psycopg[binary]>=3.1,<4.0"     "python-dotenv>=1.0,<2.0" "sqlalchemy>=2.0,<3.0"     "cachetools>=5.3,<6.0"
```

### 3️⃣ Environment Variables (`.env`)

```env
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
OPENAI_API_KEY=sk-xxxx
DATABASE_URL=postgresql+psycopg://postgres:<password>@db.<project>.supabase.co:5432/postgres
```

### 4️⃣ Run Locally

```bash
uvicorn main:app --reload
```

→ Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** for interactive OpenAPI docs.

---

## 🔗 Key Endpoints

| Endpoint            | Description                                                       |
| ------------------- | ----------------------------------------------------------------- |
| `/clusters`         | Returns AI-labeled biological subtypes (label, keywords, summary) |
| `/clusters/{id}`    | Returns a single subtype by cluster number                        |
| `/papers-sb`        | Returns papers from Supabase (filtered by cluster, year, query)   |
| `/papers`           | SQLAlchemy-based paper endpoint (legacy DB path)                  |
| `/papers/search?q=` | Keyword search with author/year filters                           |
| `/stats`            | Dataset statistics (year counts, author frequency)                |
| `/cache/status`     | View cache state + TTL                                            |
| `/cache/clear`      | Manually flush cache                                              |

---

## 🧮 Database Schema (Supabase)

| Table              | Description                                                |
| ------------------ | ---------------------------------------------------------- |
| `papers`           | Core papers (title, abstract, authors, embedding, cluster) |
| `subtype_clusters` | Cluster metadata (label, keywords, summary)                |
| `summaries`        | Technical + patient summaries by PMID                      |
| `datasets`         | Import metadata (model names, counts)                      |

---

## 🧬 AI Cure Features

| Feature                                | Description                                     |
| -------------------------------------- | ----------------------------------------------- |
| **Phase 1 – Data Pipeline**            | Fetch + summarize papers via Hugging Face       |
| **Phase 2 – Clustering**               | UMAP + HDBSCAN semantic grouping                |
| **Phase 3 – Labeling & Summarization** | GPT mechanistic labels + cluster summaries      |
| **Phase 4 – API Integration**          | `/clusters` and `/papers-sb` routes complete    |
| **Phase 4C – UI Explorer (next)**      | Next.js frontend for visual subtype exploration |

---

## 🧪 Testing & CI

```bash
pytest -v
```

All tests run automatically on commit via GitHub Actions.

---

## 🗺️ Roadmap (Next Phases)

| Phase  | Focus                                                 |
| ------ | ----------------------------------------------------- |
| **4C** | Next.js UI integration (subtypes + papers view)       |
| **4D** | UMAP 2D visualization (Plotly scatter + click filter) |
| **5**  | Trend analytics dashboard (`/stats` + charts)         |
| **6**  | Public REST docs + API keys                           |
| **7**  | User feedback + dataset submission portal             |

---

## 💖 Contributing

Contributions welcome — code, data, docs, or design.  
Help make ME/CFS research **open, accessible, and understandable** for everyone.

---

## 📜 License

MIT License © 2025 Jonathan Spruance  
_Built with care to accelerate ME/CFS research for the global community._
