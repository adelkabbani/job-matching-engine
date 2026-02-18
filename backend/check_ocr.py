
import sys
import shutil
import pytesseract
from PIL import Image

# Force stdout flush
sys.stdout.reconfigure(line_buffering=True)

# Common Installation Paths on Windows
PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\PC\AppData\Local\Tesseract-OCR\tesseract.exe"
]

def check_tesseract():
    print("--- 🔍 Tesseract Availability Check ---")
    
    # 1. Check PATH
    tess_path = shutil.which("tesseract")
    if tess_path:
        print(f"✅ Found in PATH: {tess_path}")
    else:
        print("⚠️ Not found in system PATH.")
        
        # 2. Check Common Locations
        for p in PATHS:
            try:
                with open(p, "rb"):
                    print(f"✅ Found at: {p}")
                    pytesseract.pytesseract.tesseract_cmd = p
                    tess_path = p
                    break
            except FileNotFoundError:
                pass
                
    if not tess_path:
        print("❌ Tesseract Not Found. Please install it manually.")
        print("🔗 Download: https://github.com/UB-Mannheim/tesseract/wiki")
        return False
        
    # 3. Verify Execution
    try:
        ver = pytesseract.get_tesseract_version()
        print(f"✅ Executable works! Version: {ver}")
        return True
    except Exception as e:
        print(f"❌ Error running tesseract: {e}")
        return False

if __name__ == "__main__":
    check_tesseract()
