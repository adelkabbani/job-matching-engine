
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Checking API Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("❌ No API Key found in environment variables.")
    exit(1)

genai.configure(api_key=api_key)

try:
    with open("test_gemini_result.txt", "w", encoding='utf-8') as f:
        f.write("Available models:\n")
        models_found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"- {m.name}\n")
                models_found = True
        
        if not models_found:
             f.write("No models found with generateContent support.\n")

    # Try gemini-1.5-flash-latest just in case
    print("Trying gemini-1.5-flash-latest...")
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    response = model.generate_content("Hello")
    with open("test_gemini_result.txt", "a", encoding='utf-8') as f:
        f.write("\nSuccess with gemini-1.5-flash-latest")
        
except Exception as e:
    with open("test_gemini_result.txt", "a", encoding='utf-8') as f:
        f.write(f"\nError with fallback: {e}")
    print(f"❌ Error: {e}", flush=True)
    with open("test_gemini_result.txt", "a", encoding='utf-8') as f:
        f.write(f"\nError: {e}")

