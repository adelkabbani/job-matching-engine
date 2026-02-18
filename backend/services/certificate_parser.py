
import os
import pytesseract
from PIL import Image
import io
import fitz  # PyMuPDF
from typing import Dict, Any

# Configure Tesseract path if verified
DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(DEFAULT_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_PATH

def parse_certificate(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Parses a certificate file (PDF or Image) to extract text.
    Returns a dictionary with extracted text and basic metadata.
    
    Strategy:
    1. If Image (jpg, png, etc.): Run Tesseract OCR directly.
    2. If PDF:
       a. Try extracting text directly.
       b. If text is empty or too short, render page to image and run OCR (requires PyMuPDF).
    """
    
    ext = filename.split('.')[-1].lower()
    text = ""
    method = "unknown"
    
    try:
        if ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp']:
            # Image OCR
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            method = "ocr_image"
            
        elif ext == 'pdf':
            # PDF Processing
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                full_text = []
                for page in doc:
                    page_text = page.get_text()
                    if page_text.strip():
                        # Native text found
                        full_text.append(page_text)
                    else:
                        # Fallback: Render page to image for OCR
                        # Zoom factor for better quality
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img_data = pix.tobytes("png")
                        image = Image.open(io.BytesIO(img_data))
                        ocr_text = pytesseract.image_to_string(image)
                        full_text.append(ocr_text)
                
                text = "\n".join(full_text)
                method = "pdf_text_or_ocr"
        
        else:
            return {"error": "Unsupported file format for certificate"}

        # Basic Metadata Extraction (Naive)
        # We can improve this with Regex later or LLM
        return {
            "text": text.strip(),
            "method": method,
            "char_count": len(text),
            "filename": filename
        }

    except Exception as e:
        print(f"Error parsing certificate {filename}: {e}")
        return {
            "text": "",
            "error": str(e),
            "method": "failed"
        }
