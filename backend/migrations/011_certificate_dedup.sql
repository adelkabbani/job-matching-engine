-- File: backend/migrations/011_certificate_dedup.sql
-- Purpose: Add fingerprint column for certificate deduplication
-- Run this in Supabase SQL Editor

-- Add fingerprint column for deduplication
ALTER TABLE certificate_structured_data 
ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(16);

-- Create unique index to prevent duplicates
-- This ensures same certificate (title + issuer + date) can't be added twice for same user
CREATE UNIQUE INDEX IF NOT EXISTS idx_cert_fingerprint_user 
ON certificate_structured_data(user_id, fingerprint);

-- Note: Existing certificates will have NULL fingerprints
-- They will get fingerprints when re-analyzed or can be backfilled manually
