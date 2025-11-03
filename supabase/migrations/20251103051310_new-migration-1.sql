-- ==========================================
-- Combined migration: paper_summaries, mechanism_graph, paper_mechanisms
-- Creates tables with paper_pmid (text) referencing papers(pmid)
-- ==========================================

-- 1. paper_summaries table
create table if not exists public.paper_summaries (
  id uuid primary key default gen_random_uuid(),
  paper_pmid text not null references public.papers(pmid) on delete cascade,

  provider text not null default 'openai',
  model text not null default 'gpt-5',

  one_sentence text not null,
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

-- 2. mechanism_nodes table
create table if not exists public.mechanism_nodes (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamp with time zone default timezone('utc', now())
);

-- 3. biomarker_nodes table
create table if not exists public.biomarker_nodes (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamp with time zone default timezone('utc', now())
);

-- 4. mechanism_edges table
create table if not exists public.mechanism_edges (
  id uuid primary key default gen_random_uuid(),

  paper_pmid text not null references public.papers(pmid) on delete cascade,
  mechanism_id uuid references public.mechanism_nodes(id) on delete set null,
  biomarker_id uuid references public.biomarker_nodes(id) on delete set null,

  created_at timestamp with time zone default timezone('utc', now())
);

-- Speeds up graph traversal
create index if not exists idx_mechanism_edges_paper_id
  on public.mechanism_edges(paper_pmid);

create index if not exists idx_mechanism_edges_mechanism_id
  on public.mechanism_edges(mechanism_id);

create index if not exists idx_mechanism_edges_biomarker_id
  on public.mechanism_edges(biomarker_id);

-- 5. paper_mechanisms table
create table if not exists public.paper_mechanisms (
  id uuid primary key default gen_random_uuid(),

  -- Foreign key to papers table using pmid; keep nullable for compatibility.
  paper_pmid text null references public.papers(pmid) on delete cascade,

  -- Always record the PMID explicitly.
  pmid text not null,

  -- Hybrid output
  categories   text[] not null default '{}',  -- fixed buckets: immune, mitochondrial, vascular, autonomic, neurological, metabolic, oxidative_stress, infectious_trigger
  mechanisms   text[] not null default '{}',  -- free-text mechanisms e.g., "NK cell cytotoxicity deficit", "PDH inhibition", "microclots"
  biomarkers   text[] not null default '{}',  -- free-text biomarkers e.g., "IL-6", "NK cells", "lactate", "ET-1"
  confidence   numeric    default 0.0,        -- model-level confidence (0..1)

  provider     text not null default 'openai',
  model        text not null default 'gpt-5',

  raw_output   jsonb,                         -- full model JSON for audit/debug
  created_at   timestamptz not null default now()
);

-- One row per (pmid, provider, model)
create unique index if not exists uq_paper_mechanisms_pmid_provider_model
  on public.paper_mechanisms (pmid, provider, model);

create index if not exists idx_paper_mechanisms_pmid
  on public.paper_mechanisms (pmid);

create index if not exists idx_paper_mechanisms_categories
  on public.paper_mechanisms using gin (categories);

create index if not exists idx_paper_mechanisms_biomarkers
  on public.paper_mechanisms using gin (biomarkers);

