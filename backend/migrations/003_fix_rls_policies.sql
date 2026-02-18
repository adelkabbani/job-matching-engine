-- Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Users can view own documents" ON documents;
DROP POLICY IF EXISTS "Users can upload own documents" ON documents;
DROP POLICY IF EXISTS "Service role full access" ON documents;

-- Re-enable RLS (idempotent)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- 1. Review: Users can see/upload their OWN documents
CREATE POLICY "Users can view own documents" 
ON documents FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can upload own documents" 
ON documents FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- 2. Admin: Service Role has FULL ACCESS
CREATE POLICY "Service role full access" 
ON documents FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);
