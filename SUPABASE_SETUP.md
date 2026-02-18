# Supabase Setup Instructions

## 1. Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Choose a name (e.g., "hyperapply")
4. Set a strong database password
5. Select a region close to you
6. Wait for project to initialize (~2 minutes)

## 2. Get Credentials

1. Go to **Project Settings** → **API**
2. Copy:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **Service role key** (under "Project API keys" → "service_role")

## 3. Configure Backend

1. Create `backend/.env` file (copy from `.env.example`):
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_SERVICE_KEY=your-service-role-key-here
   ```

2. Install dependencies:
   ```powershell
   pip install -r backend/requirements.txt
   ```

## 4. Run SQL Migration

1. Go to Supabase **SQL Editor**
2. Click "New Query"
3. Copy the contents of `backend/migrations/001_initial_schema.sql`
4. Paste and click "Run"
5. Verify table created: go to **Table Editor** → you should see `documents`

## 5. Create Storage Bucket

1. Go to **Storage** in Supabase dashboard
2. Click "Create Bucket"
3. Name: `documents`
4. **Public bucket**: No (keep private)
5. **File size limit**: 50 MB
6. Click "Create"

## 6. Test Upload

1. Start backend: `python backend/main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Go to http://localhost:3000/dashboard
4. Upload a CV
5. Check:
   - Supabase Storage → `documents` bucket → file should appear
   - Supabase Table Editor → `documents` table → row should appear

## 7. Verify Health

Open http://localhost:8000/api/health/uploads

Should return:
```json
{
  "status": "ok",
  "supabase_connected": true,
  "storage_buckets": ["documents"]
}
```

---

## Troubleshooting

**"Supabase not configured"**
→ Check `backend/.env` has correct URL and key

**"Bucket not found"**
→ Create `documents` bucket in Supabase Storage

**"Table doesn't exist"**
→ Run the SQL migration in SQL Editor
