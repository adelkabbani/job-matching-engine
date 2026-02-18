-- File: backend/migrations/002_auth_schema.sql

-- 1. PROFILES TABLE (Public profile info)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Automation: Create profile when a new user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, avatar_url)
  VALUES (
    new.id, 
    new.email, 
    new.raw_user_meta_data->>'full_name', 
    new.raw_user_meta_data->>'avatar_url'
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger the function on every new sign up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();


-- 2. JOBS TABLE (Jobs the user is tracking)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    job_url TEXT,
    status TEXT DEFAULT 'saved' CHECK (status IN ('saved', 'applied', 'interview', 'offer', 'rejected')),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);


-- 3. APPLICATIONS TABLE (Linking Documents to Jobs)
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE NOT NULL,
    cv_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    cover_letter_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- 4. ENABLE RLS (Security Policies)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
-- documents table already has RLS enabled from Phase 1


-- 5. DEFINE SECURITY POLICIES (Users see ONLY their own data)

-- Profiles: View and Edit own profile
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Documents: View and Insert own documents
-- (Note: Service Role can still bypass this for admin tasks)
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can upload own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Jobs: Full access to own jobs
CREATE POLICY "Users can manage own jobs" ON jobs
    FOR ALL USING (auth.uid() = user_id);

-- Applications: Full access to own applications via jobs linkage
-- (Simplified: For now, we rely on the application being linked to a job you own)
-- A more robust policy would check the join, but RLS on joins can be complex.
-- For simplicity in Phase 2, we'll verify ownership in backend logic or use a simpler policy if user_id was on applications.
-- Let's add user_id to applications to make RLS simple and secure.
ALTER TABLE applications ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE POLICY "Users can manage own applications" ON applications
    FOR ALL USING (auth.uid() = user_id);
