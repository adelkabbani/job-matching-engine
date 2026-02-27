-- Add a Unique Constraint to the cv_versions table on (user_id, job_id)
ALTER TABLE cv_versions ADD CONSTRAINT cv_versions_user_job_idx UNIQUE (user_id, job_id);

-- Add a Unique Constraint to the cover_letters table on (user_id, job_id, variant)
ALTER TABLE cover_letters ADD CONSTRAINT cover_letters_user_job_variant_idx UNIQUE (user_id, job_id, variant);

-- Ensure the applications table includes the success_screenshot_path column
ALTER TABLE applications ADD COLUMN IF NOT EXISTS success_screenshot_path TEXT;
