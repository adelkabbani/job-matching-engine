import sys
import os

def read_encoded_file(path):
    encodings = ['utf-16le', 'utf-16', 'utf-8', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                content = f.read()
                print(f"--- Decoded {path} with {enc} ---")
                return content
        except Exception:
            continue
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_any_encoded.py <file_path>")
        sys.exit(1)
    
    path = sys.argv[1]
    content = read_encoded_file(path)
    if content:
        output_path = f"readable_{os.path.basename(path)}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Saved to {output_path}")
    else:
        print(f"❌ Failed to decode {path}")
