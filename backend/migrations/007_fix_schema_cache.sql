-- 1. Ensure the column exists (Idempotent)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS openrouter_key TEXT;

-- 2. FORCE Schema Cache Reload (The Fix)
NOTIFY pgrst, 'reload config';
