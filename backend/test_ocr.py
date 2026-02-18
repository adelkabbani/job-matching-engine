
import pytesseract
from PIL import Image
import os
import sys

# Windows Path Configuration
# Try to auto-detect or use default
DEFAULT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(DEFAULT_PATH):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_PATH

def test_ocr():
    print("--- 🔬 Testing OCR Extraction ---")
    
    # Create a dummy image with text if no sample provided
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create larger image for better OCR
        img = Image.new('RGB', (800, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        # Try to load Arial (Windows standard)
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except IOError:
            font = ImageFont.load_default()
            print("⚠️ Using default font (might be too small)")
            
        d.text((50, 50), "ANTIGRAVITY OCR", fill=(0, 0, 0), font=font)
        
        # Use current directory to save sample (simpler for test)
        img_path = "test_sample.png"
        img.save(img_path)
        print(f"✅ Created sample image: {img_path}")
        
        # Run OCR
        text = pytesseract.image_to_string(Image.open(img_path))
        print(f"📝 Extracted Text:\n{text.strip()}")
        
        
        if "ANTIGRAVITY" in text.upper():
            print("✅ OCR Verification SUCCESS!")
        else:
            print("❌ OCR Verification FAILED (Text mismatch)")
            
    except ImportError:
        print("❌ PIL (Pillow) not installed.")
    except Exception as e:
        print(f"❌ OCR Error: {e}")

if __name__ == "__main__":
    test_ocr()
