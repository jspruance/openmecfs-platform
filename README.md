# 🌍 Open ME/CFS API

**Open ME/CFS** is an open-source initiative combining **AI, open data, and community collaboration** to accelerate research and awareness around **Myalgic Encephalomyelitis / Chronic Fatigue Syndrome (ME/CFS)**.

This repository contains the **FastAPI backend** that powers the Open ME/CFS data platform — serving AI-summarized research papers as structured, queryable data.

---

## 🧠 Project Overview

### 💡 Mission

> Democratize ME/CFS research by connecting patients, advocates, and researchers through open science and accessible data.

The API makes it possible to **search**, **filter**, and **analyze** AI-generated summaries of ME/CFS research papers from PubMed — without needing to install any AI models or scripts.

---

## ⚙️ Tech Stack

| Layer                  | Tools / Frameworks                          | Purpose                                |
| ---------------------- | ------------------------------------------- | -------------------------------------- |
| **Backend**            | FastAPI + Uvicorn                           | REST API server                        |
| **Data Layer**         | JSON (local) → Postgres / Supabase (future) | Research paper storage                 |
| **AI Summaries**       | Hugging Face Transformers (BART, T5)        | Technical & patient-friendly summaries |
| **Frontend (Planned)** | Next.js / React                             | Community and research dashboard       |

---

## 🧩 Folder Structure

```
openmecfs-platform/
│
├── main.py                # FastAPI entry point
├── routes/
│   └── papers.py          # API endpoints for papers & search
├── utils/
│   └── loader.py          # Loads summarized JSON data
├── data/
│   └── mecfs_papers_summarized_2025-10-11.json
└── README.md
```

---

## 🚀 Getting Started

### 1️⃣ Create environment

```bash
python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows
```

### 2️⃣ Install dependencies

```bash
pip install fastapi uvicorn
```

### 3️⃣ Run the API

```bash
uvicorn main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive Swagger UI.

---

## 🔗 Endpoints

| Endpoint            | Description                         |
| ------------------- | ----------------------------------- |
| `/`                 | Welcome + API info                  |
| `/papers`           | Paginated list of all papers        |
| `/papers/{pmid}`    | Details for a specific paper        |
| `/papers/search?q=` | Search across abstracts & summaries |
| `/papers/meta`      | Dataset & model metadata            |

---

## 📦 Data Source

The summarized JSON file (from Phase 2) is produced by:

```
summarizer.py → data/mecfs_papers_summarized_YYYY-MM-DD.json
```

The API loads this automatically at startup.  
If no file is found, it starts in empty mode with a friendly message.

---

## 📈 Scaling Plan

### 1️⃣ Fetching More Papers

Yes — the next iteration of the data-fetch pipeline (`fetch_pubmed.py`) will:

- Use **pagination via Entrez API** (`retstart` parameter) to fetch **thousands** of results.
- Store each batch incrementally.
- Avoid rate limits by batching requests (100–200 at a time).

This will allow **ongoing updates** as new ME/CFS studies are published.

### 2️⃣ Database Integration

For now, **JSON files** are totally fine (Phase 2–3 prototype).  
Once you have stable summaries, we’ll:

- Migrate to **Postgres / Supabase**
- Add **API writes + refresh jobs**
- Enable **search, filters, and analytics** via SQL

That becomes **Phase 4**.

---

## 🌐 Future Frontend

Once the backend stabilizes, the **Next.js frontend** will:

- Display AI summaries for each paper
- Provide topic filters (immune, mitochondria, neurological, etc.)
- Offer both “technical” and “patient-friendly” reading modes
- Show donation transparency metrics (later phase)

---

## 💖 Contributing

Contributions welcome — whether technical (code, data) or community (outreach, design).  
Join in to help make ME/CFS research **open, accessible, and understandable** for everyone.

---

## 📜 License

MIT License © 2025 Jonathan Spruance  
_Built with care to accelerate ME/CFS research for the global community._
