import os

def unlock_applied_status():
    """
    Prints the exact SQL to fix the 'applied' status constraint.
    """
    print("\n--- 🚧 DATABASE LOCK DETECTED ---")
    print("The system cannot record 'applied' status because of a check constraint.")
    print("Please run this EXACT SQL in your Supabase Dashboard (SQL Editor):")
    print("-" * 50)
    print("""
ALTER TABLE public.jobs DROP CONSTRAINT IF EXISTS jobs_status_check;
ALTER TABLE public.jobs ADD CONSTRAINT jobs_status_check 
CHECK (status IN ('scraped', 'shortlisted', 'applying', 'applied', 'failed'));

COMMENT ON TABLE public.jobs IS 'Pipeline unlocked for all application stages';
    """)
    print("-" * 50)
    print("Once run, Run #7 will succeed in saving status!")

if __name__ == "__main__":
    unlock_applied_status()
