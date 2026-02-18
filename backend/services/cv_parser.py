
import io
from pypdf import PdfReader
from docx import Document

def parse_cv(file_bytes: bytes, filename: str) -> str:
    """
    Extracts raw text from PDF or DOCX file bytes.
    Returns empty string if extraction fails or format is unsupported.
    """
    filename = filename.lower()
    text = ""
    
    try:
        file_stream = io.BytesIO(file_bytes)
        
        if filename.endswith(".pdf"):
            reader = PdfReader(file_stream)
            for page in reader.pages:
                # Extract text and append newline
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            print(f"✅ Parsed PDF: {len(text)} chars")
                
        elif filename.endswith(".docx"):
            doc = Document(file_stream)
            for para in doc.paragraphs:
                text += para.text + "\n"
            print(f"✅ Parsed DOCX: {len(text)} chars")
        
        else:
            print(f"⚠️ Unsupported file type for parsing: {filename}")
            return ""

        return text.strip()
        
    except Exception as e:
        error_msg = f"❌ Error parsing {filename}: {e}"
        print(error_msg)
        
        # Log to file (robust path)
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Go up to backend/
        log_path = os.path.join(base_dir, "parsing_log.txt")
        
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(error_msg + "\n")
        except:
            pass
            
        return ""
