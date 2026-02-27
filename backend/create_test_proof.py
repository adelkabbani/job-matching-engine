import os

# Create dummy proof for testing the UI
logs_dir = os.path.join(os.getcwd(), ".tmp", "logs", "applications", "test_job")
os.makedirs(logs_dir, exist_ok=True)
proof_path = os.path.join(logs_dir, "success_proof.png")

with open(proof_path, "w") as f:
    f.write("Dummy proof image content")

print(f"✅ Created dummy proof at: {proof_path}")
print("You can now test the 'View Proof' button if you have a job with ID 'test_job' in your DB.")
