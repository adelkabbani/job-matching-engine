
-- Step 3: Add original_ai_data for versioning edits
ALTER TABLE cv_structured_data 
ADD COLUMN IF NOT EXISTS original_ai_data JSONB DEFAULT '{}'::jsonb;

-- Ensure RLS allows updates for owner
CREATE POLICY "Users can update their own CV data"
ON cv_structured_data FOR UPDATE
USING (auth.uid() = user_id);
