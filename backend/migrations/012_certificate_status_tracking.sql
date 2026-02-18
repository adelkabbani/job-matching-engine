-- File: backend/migrations/012_certificate_status_tracking.sql
-- Purpose: Add status tracking fields for certificate analysis
-- Run this in Supabase SQL Editor

-- Add status tracking fields to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS analysis_status TEXT DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS analysis_error TEXT,
ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMPTZ;

-- Add index for faster status queries
CREATE INDEX IF NOT EXISTS idx_documents_analysis_status 
ON documents(user_id, doc_type, analysis_status);

-- Add check constraint for valid status values
-- Note: PostgreSQL doesn't support IF NOT EXISTS for constraints, so we use DO block
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_analysis_status'
    ) THEN
        ALTER TABLE documents 
        ADD CONSTRAINT chk_analysis_status 
        CHECK (analysis_status IN ('pending', 'processing', 'done', 'failed'));
    END IF;
END $$;

-- Update existing certificate documents to have 'done' status if they have structured data
UPDATE documents d
SET analysis_status = 'done',
    analyzed_at = NOW()
WHERE doc_type = 'certificate'
  AND analysis_status = 'pending'
  AND EXISTS (
    SELECT 1 FROM certificate_structured_data csd
    WHERE csd.document_id = d.id
  );
