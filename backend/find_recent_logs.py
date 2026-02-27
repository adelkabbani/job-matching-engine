import os
import glob
from datetime import datetime

LOGS_DIR = os.path.join(os.getcwd(), ".tmp", "logs", "applications")

def find_recent_screenshots():
    all_pngs = glob.glob(os.path.join(LOGS_DIR, "**", "*.png"), recursive=True)
    if not all_pngs:
        print("No screenshots found in logs directory.")
        return

    # Sort by modification time
    all_pngs.sort(key=os.path.getmtime, reverse=True)
    
    print(f"Total screenshots found: {len(all_pngs)}")
    print("\nMost recent 10 screenshots:")
    for img in all_pngs[:10]:
        mtime = datetime.fromtimestamp(os.path.getmtime(img))
        print(f"Path: {img} | Date: {mtime}")

if __name__ == "__main__":
    find_recent_screenshots()
