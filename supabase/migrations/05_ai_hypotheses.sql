-- 05_ai_hypotheses.sql
create table if not exists public.ai_hypotheses (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  summary text,
  confidence numeric check (confidence >= 0 and confidence <= 1),
  mechanisms text[] default '{}',
  biomarkers text[] default '{}',
  citations text[] default '{}',
  created_at timestamptz default now()
);
