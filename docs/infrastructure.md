# Open ME/CFS — Platform Infrastructure (Quick Notes)

## Overview

The Open ME/CFS stack consists of:

| Layer       | Service                   | Purpose                                    |
| ----------- | ------------------------- | ------------------------------------------ |
| Frontend    | Vercel (Next.js)          | UI + client-side features                  |
| Backend API | Railway (FastAPI)         | Papers API + clustering endpoints          |
| Database    | Supabase Postgres         | Research DB + pgvector                     |
| Storage     | Supabase                  | (future: papers, embeddings)               |
| Secrets     | Vercel + Railway env vars | Secret management                          |
| AI Models   | OpenAI (temporary)        | Summaries, embeddings (later local models) |

## Current Repos

| Repo                      | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `openmecfs-ui`            | Next.js research explorer                             |
| `openmecfs-platform`      | FastAPI app that queries Supabase                     |
| `openmecfs-data-pipeline` | Python ingestion + summarization (local only for now) |

## Environment Variables

**Platform (`.env`)**

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=

DATABASE_URL=

OPENAI_API_KEY=
ADMIN_TOKEN=
```

**UI**

```
NEXT_PUBLIC_API_URL=https://<railway-app-url>
```

## Deployment Plan

| Step | Action                                      |
| ---- | ------------------------------------------- |
| 1    | Push FastAPI + Supabase keys to Railway     |
| 2    | Railway auto-builds + gives a public URL    |
| 3    | Add this URL to `.env.local` in Next app    |
| 4    | Deploy Next app on Vercel                   |
| 5    | Verify `/papers` and `/clusters` calls work |

## Roadmap (Infra)

| Phase | Items                                      |
| ----- | ------------------------------------------ |
| Now   | Railway + Supabase + Vercel                |
| Soon  | Background jobs (Celery worker + Redis)    |
| Later | Self-host local LLMs for bio summarization |
