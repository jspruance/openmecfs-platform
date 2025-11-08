-- ✅ Add timestamp for sync tracking
ALTER TABLE public.ai_hypotheses
ADD COLUMN IF NOT EXISTS last_synced_at timestamptz DEFAULT now();
