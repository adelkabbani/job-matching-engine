-- 1. Drop old policies to be safe
DROP POLICY IF EXISTS "Users can view own documents" ON documents;
DROP POLICY IF EXISTS "Users can upload own documents" ON documents;
DROP POLICY IF EXISTS "Service role full access" ON documents;
DROP POLICY IF EXISTS "Admin All" ON documents;

-- 2. Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- 3. Standard User Policies
CREATE POLICY "Users can view own documents" 
ON documents FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can upload own documents" 
ON documents FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- 4. ROBUST Admin Policy
-- Checks both the Postgres role AND the JWT claim
CREATE POLICY "Service role full access" 
ON documents FOR ALL 
USING (
  auth.role() = 'service_role' OR 
  current_setting('request.jwt.claim.role', true) = 'service_role'
) 
WITH CHECK (
  auth.role() = 'service_role' OR 
  current_setting('request.jwt.claim.role', true) = 'service_role'
);
