import os

def read_encoded_file(path):
    encodings = ['utf-16le', 'utf-16', 'utf-8', 'latin-1']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                content = f.read()
                print(f"--- Decoded with {enc} ---")
                print(content)
                return content
        except Exception:
            continue
    print("Failed to decode file with any common encoding.")
    return None

if __name__ == "__main__":
    content = read_encoded_file("pid_check.txt")
    if content:
        with open("pid_readable.txt", "w", encoding="utf-8") as f:
            f.write(content)
