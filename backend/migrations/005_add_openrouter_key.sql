-- Add OpenRouter Key to Profiles
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS openrouter_key TEXT;

-- Validate logic:
-- The existing RLS policies on 'profiles' table allow users to:
-- 1. SELECT their own profile (auth.uid() = id)
-- 2. UPDATE their own profile (auth.uid() = id)
-- This is exactly what we want. No new policies needed.
