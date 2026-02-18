-- File: backend/migrations/013_job_matching.sql
-- Purpose: Create tables for job matching engine with robust column addition
-- Run this in Supabase SQL Editor

-- 1. Create Jobs table if it doesn't exist
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  description TEXT NOT NULL,
  url TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Add missing columns to jobs table (in case it already existed)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS location TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS remote_ok BOOLEAN DEFAULT false;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'english';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS experience_level TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS match_score INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS matched_skills TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS missing_skills TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS strengths_summary TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS filtered_out BOOLEAN DEFAULT false;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS filter_reason TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS raw_data JSONB;

-- 3. Create Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_user_score ON jobs(user_id, match_score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_user_created ON jobs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_filtered ON jobs(user_id, filtered_out);

-- 4. Create Job filters table
CREATE TABLE IF NOT EXISTS job_filters (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE UNIQUE,
  languages TEXT[] DEFAULT ARRAY['english'],
  locations TEXT[] DEFAULT ARRAY['berlin', 'remote'],
  role_keywords TEXT[] DEFAULT ARRAY['data', 'ai', 'analytics', 'it'],
  experience_levels TEXT[] DEFAULT ARRAY['junior', 'mid'],
  visa_friendly BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Create default filters for existing users
INSERT INTO job_filters (user_id)
SELECT id FROM profiles
WHERE NOT EXISTS (
  SELECT 1 FROM job_filters WHERE job_filters.user_id = profiles.id
)
ON CONFLICT (user_id) DO NOTHING;
