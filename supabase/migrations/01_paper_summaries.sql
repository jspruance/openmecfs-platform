-- ==========================================
-- 01_paper_summaries.sql
-- Stores AI-generated summaries & evidence
-- ==========================================

create table if not exists public.paper_summaries (
  id uuid primary key default gen_random_uuid(),
  paper_pmid text not null references public.papers(pmid) on delete cascade,

  provider text not null default 'openai',
  model text not null default 'gpt-5',

  one_sentence text not null,
  technical_summary text,
  patient_summary text,
  mechanisms text[] not null default '{}',
  biomarkers text[] not null default '{}',
  confidence numeric default 0.0,
  tags text[] not null default '{}',

  -- prevents recomputation for same input
  hash text not null unique,

  created_at timestamp with time zone default timezone('utc', now())
);

-- Speed up lookup by paper
create index if not exists idx_paper_summaries_paper_id
  on public.paper_summaries (paper_pmid);

-- Idempotency: ensure only one summary per paper hash
create unique index if not exists idx_paper_summaries_hash
  on public.paper_summaries (hash);
