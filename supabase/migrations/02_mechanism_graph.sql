-- ==========================================
-- 02_mechanism_graph.sql
-- Mechanism & biomarker graph tables
-- ==========================================

-- Mechanisms (immune dysfunction, mitochondrial impairment, etc.)
create table if not exists public.mechanism_nodes (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamp with time zone default timezone('utc', now())
);

-- Biomarkers (IL-6, NK cell function, lactate, etc.)
create table if not exists public.biomarker_nodes (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamp with time zone default timezone('utc', now())
);

-- Edges linking evidence → mechanistic concepts → biomarkers
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
