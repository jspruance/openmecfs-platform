# 🌍 Open ME/CFS API

**Open ME/CFS** is an open-source initiative combining **AI, open data, and community collaboration** to accelerate research and awareness around **Myalgic Encephalomyelitis / Chronic Fatigue Syndrome (ME/CFS)**.

This repository contains the **FastAPI backend** that powers the Open ME/CFS data platform — serving AI-summarized, vector-searchable research papers as structured, queryable data.

---

## 🧠 Mission

> Democratize ME/CFS research by connecting patients, advocates, and researchers through open science and accessible data.

The API lets anyone **search**, **filter**, and **analyze** ME/CFS research using both keyword and semantic (AI-embedding) search — no model setup required.

---

## ⚙️ Tech Stack

| Layer                  | Tools / Frameworks                   | Purpose                                |
| ---------------------- | ------------------------------------ | -------------------------------------- |
| **Backend**            | FastAPI + Uvicorn                    | REST API server                        |
| **Database**           | Supabase (PostgreSQL + pgvector)     | Paper storage + semantic embeddings    |
| **AI Summaries**       | Hugging Face Transformers (BART, T5) | Technical + patient-friendly summaries |
| **Semantic Search**    | OpenAI Embeddings API                | Vector search & hybrid ranking         |
| **Caching / Stats**    | In-memory cache + FastAPI routes     | Quick response + metrics               |
| **Testing / CI**       | Pytest + GitHub Actions              | Regression tests on commit             |
| **Frontend (Planned)** | Next.js / React                      | Research & community dashboard         |

---

## 🧩 Folder Structure

```
openmecfs-platform/
│
├── main.py                     # FastAPI entry point
├── routes/
│   ├── papers.py               # Paper endpoints (search, semantic, hybrid)
│   ├── stats.py                # Dataset stats & cache status
│   └── cache.py                # Cache control endpoints
│
├── utils/
│   ├── db.py                   # Supabase client + query helpers
│   ├── cache.py                # In-memory TTL cache
│   └── generate_embeddings.py  # One-time embedding generator
│
├── tests/
│   └── test_papers_api.py      # Pytest API regression suite
│
├── data/
│   └── mecfs_papers_summarized_2025-10-11.json
│
├── .env                        # Secrets (SUPABASE_URL, OPENAI_API_KEY, etc.)
└── requirements.txt            # Python dependencies
```

---

## 🚀 Getting Started

### 1️⃣ Create environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate         # Windows
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

If setting up fresh:

```bash
pip install fastapi uvicorn supabase openai python-dotenv pytest
```

### 3️⃣ Environment variables (`.env`)

```env
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
OPENAI_API_KEY=sk-xxxx
```

### 4️⃣ Run API locally

```bash
uvicorn main:app --reload
```

Then open → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔗 Key Endpoints

| Endpoint              | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| `/papers`             | Paginated list of papers                                         |
| `/papers/{pmid}`      | Single paper + summaries                                         |
| `/papers/search?q=`   | Keyword search with author/year filters                          |
| `/papers/suggest?q=`  | Autocomplete title suggestions                                   |
| `/papers/semantic?q=` | **Semantic vector search** via OpenAI embeddings + pgvector      |
| `/papers/hybrid?q=`   | **Hybrid search** combining keyword + semantic ranking           |
| `/papers/meta`        | Dataset metadata (model info + import timestamp)                 |
| `/stats`              | API + dataset statistics (total papers, with/without embeddings) |
| `/cache/status`       | View cache state and TTL                                         |
| `/cache/clear`        | Programmatically flush cache                                     |

---

## 🧮 Database Schema (Supabase)

| Table       | Description                                                   |
| ----------- | ------------------------------------------------------------- |
| `papers`    | Core papers (title, abstract, authors_text, embedding vector) |
| `summaries` | Technical & patient friendly AI summaries by PMID             |
| `datasets`  | Metadata on imported batches (model names, counts)            |

Includes the RPC function:

```sql
match_papers(query_embedding vector(1536), match_count int)
```

→ returns top-N papers ranked by cosine similarity.

---

## 🧠 AI Features

- 🧩 **AI Summarization** – Two summary styles (technical & plain language)
- 🧬 **Semantic Search** – OpenAI Embeddings (`text-embedding-3-small`)
- 🔍 **Hybrid Search** – Weighted keyword + vector similarity
- ⚡ **Caching** – Instant repeat queries & precomputed stats
- 📊 **Stats Endpoints** – Paper count & embedding coverage

---

## 🧪 Testing and CI

Run local tests:

```bash
pytest -v
```

All tests auto-run on each Git commit via GitHub Actions.

---

## 🗺️ Next Milestones

| Phase  | Focus                                   |
| ------ | --------------------------------------- |
| **8**  | Hybrid search caching + ranking weights |
| **9**  | Public REST Docs + API Key auth         |
| **10** | Next.js frontend dashboard              |
| **11** | User feedback + dataset submission flow |

---

## 💖 Contributing

Contributions welcome — code, data, docs, or design.  
Help make ME/CFS research **open, accessible, and understandable** for everyone.

---

## 📜 License

MIT License © 2025 Jonathan Spruance  
_Built with care to accelerate ME/CFS research for the global community._
