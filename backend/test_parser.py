
import os
import sys
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.services.cv_parser import parse_cv
except ImportError:
    # Fallback for running inside backend dir
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from services.cv_parser import parse_cv

def test_file(filepath):
    print(f"\n📂 Testing: {filepath}")
    if not os.path.exists(filepath):
        print("❌ File not found.")
        return

    try:
        with open(filepath, "rb") as f:
            file_bytes = f.read()
            filename = os.path.basename(filepath)
            
            print(f"   Type: {filename.split('.')[-1]}")
            print(f"   Size: {len(file_bytes)} bytes")
            
            text = parse_cv(file_bytes, filename)
            
            if text:
                print(f"   ✅ SUCCESS: Extracted {len(text)} characters")
                print(f"   --- Text Preview ---\n{text[:200]}...\n--------------------")
            else:
                print("   ⚠️  WARNING: No text extracted (or empty).")
                
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test CV Parser')
    parser.add_argument('file', nargs='?', help='Path to PDF or DOCX file')
    args = parser.parse_args()
    
    if args.file:
        test_file(args.file)
    else:
        print("Usage: python backend/test_parser.py <path_to_cv>")
