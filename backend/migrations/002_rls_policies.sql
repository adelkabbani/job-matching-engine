-- Enable RLS (in case it was disabled)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- 1. Allow Users to View their OWN documents
CREATE POLICY "Users can view own documents" 
ON documents FOR SELECT 
USING (auth.uid() = user_id);

-- 2. Allow Users to Upload their OWN documents
CREATE POLICY "Users can upload own documents" 
ON documents FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- 3. Allow Service Role (Admin/Backend) to do ANYTHING
-- This fixes the verification script and ensures backend admin tasks work
CREATE POLICY "Service role full access" 
ON documents FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);
