-- File: backend/migrations/014_apply_assistant.sql
-- Purpose: Support for shortlist workflow, application tracking, and automated question bank

-- 1. Update jobs table with status and Easy Apply flag
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'interested'; -- 'interested', 'shortlisted', 'rejected'
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_easy_apply BOOLEAN DEFAULT false;

-- Add index for status filtering
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(user_id, status);

-- 2. Create Applications table to track submitted jobs
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    
    company TEXT NOT NULL,
    role_title TEXT NOT NULL,
    match_score INTEGER,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'applied', -- 'applied', 'interviewing', 'offered', 'rejected'
    
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick tracking
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);

-- 3. Create Question Bank for LinkedIn "Easy Apply" extra questions
CREATE TABLE IF NOT EXISTS linkedin_question_bank (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    category TEXT DEFAULT 'general', -- 'experience', 'visa', 'salary', 'technical'
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure same user doesn't have duplicate semi-identical questions
    UNIQUE(user_id, question_text)
);

CREATE INDEX IF NOT EXISTS idx_question_bank_user ON linkedin_question_bank(user_id);
