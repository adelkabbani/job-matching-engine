-- 1. Reset Policies
DROP POLICY IF EXISTS "Users can view own documents" ON documents;
DROP POLICY IF EXISTS "Users can upload own documents" ON documents;
DROP POLICY IF EXISTS "Service role full access" ON documents;
DROP POLICY IF EXISTS "Admin All" ON documents;
DROP POLICY IF EXISTS "Admin" ON documents; -- Just in case

-- 2. Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- 3. Strict User Policies (No explicit Admin policy, relying on Service Key bypass)
CREATE POLICY "Users can view own documents" 
ON documents FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can upload own documents" 
ON documents FOR INSERT 
WITH CHECK (auth.uid() = user_id);
