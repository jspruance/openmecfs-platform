-- 03_paper_mechanisms.sql

create table if not exists public.paper_mechanisms (
  id uuid primary key default gen_random_uuid(),

  -- Prefer paper_id if your `papers` table has an id column; keep nullable for compatibility.
  paper_id uuid null references public.papers(id) on delete cascade,

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
