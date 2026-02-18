-- Add content_text to documents table for raw extraction
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS content_text TEXT;

-- Create table for structured CV data (result of LLM extraction)
CREATE TABLE IF NOT EXISTS cv_structured_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    parsed_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id)
);

-- RLS Policies for cv_structured_data
ALTER TABLE cv_structured_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own CV data"
ON cv_structured_data FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own CV data"
ON cv_structured_data FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own CV data"
ON cv_structured_data FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own CV data"
ON cv_structured_data FOR DELETE
USING (auth.uid() = user_id);
