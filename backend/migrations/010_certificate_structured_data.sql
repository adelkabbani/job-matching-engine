-- File: backend/migrations/010_certificate_structured_data.sql
-- Purpose: Create table to store structured certificate data extracted from OCR text
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS certificate_structured_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    parsed_data JSONB NOT NULL,
    original_ocr_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_cert_structured_user ON certificate_structured_data(user_id);
CREATE INDEX idx_cert_structured_doc ON certificate_structured_data(document_id);

-- Enable RLS
ALTER TABLE certificate_structured_data ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own certificate data"
ON certificate_structured_data FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own certificate data"
ON certificate_structured_data FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own certificate data"
ON certificate_structured_data FOR UPDATE
USING (auth.uid() = user_id);
