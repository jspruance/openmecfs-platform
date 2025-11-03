create table if not exists paper_graph (
  id uuid primary key default gen_random_uuid(),
  paper_pmid text not null references papers(pmid) on delete cascade,

  mechanism text,
  biomarker text,

  -- "paper→mechanism", "mechanism→biomarker"
  edge_type text not null,

  created_at timestamptz default now()
);

create index if not exists idx_paper_graph_pmid on paper_graph(paper_pmid);
