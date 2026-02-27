# File: backend/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Security, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import json
import os
from pathlib import Path
import random
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import traceback
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from datetime import datetime
from services.linkedin_assistant import launch_linkedin_browser, stop_linkedin_browser, capture_current_search_results

# Load environment variables
load_dotenv()

# Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("⚠️  WARNING: Supabase credentials not found in .env file")
    print("   Create backend/.env with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY")
    supabase: Client = None
else:
    # Service role client (admin) - used for uploads bypassing RLS
    supabase: Client = create_client(url, key)
    print(f"✅ Supabase client initialized: {url}")
    
    # ------------------ DEBUG HOOK ------------------
    try:
        _d = supabase.table('jobs').select('status').limit(10).execute()
        print(f"🔥 LIVE DATABASE VALID STATUSES: {list(set([x.get('status') for x in _d.data if x.get('status')]))}")
        print(f"🔥 TOTAL JOBS: {len(_d.data)}")
        print("="*60)
    except Exception as e:
        print(f"🔥 DEBUG HOOK ERROR: {e}")
    # ------------------------------------------------

# Import Phase 9 Services
try:
    from services.cv_tailor import tailor_cv
    from services.llm import generate_cover_letter
    from services.doc_generator import generate_cv_docx, generate_cover_letter_docx
except ImportError:
    # Use backend prefix if needed
    from backend.services.cv_tailor import tailor_cv
    from backend.services.llm import generate_cover_letter
    from backend.services.doc_generator import generate_cv_docx, generate_cover_letter_docx

app = FastAPI()

# Mount static logs directory for proof access
LOGS_DIR = os.path.join(os.getcwd(), ".tmp", "logs", "applications")
os.makedirs(LOGS_DIR, exist_ok=True)
app.mount("/api/logs", StaticFiles(directory=LOGS_DIR), name="logs")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Scheme
security = HTTPBearer()

import jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifies the JWT token locally without network calls to bypass IPv6 errors."""
    token = credentials.credentials
    try:
        # Decode the JWT token locally (bypassing Supabase network fetch)
        # We extract the 'sub' claim which is the user ID. 
        # For local development we skip signature verification if JWT_SECRET is missing.
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        if jwt_secret:
            decoded_token = jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="authenticated")
        else:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            
        user_id = decoded_token.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        # Create a mock user object that mimics what Supabase auth returns
        class MockUser:
            def __init__(self, uid):
                self.id = uid
        return MockUser(user_id)
        
    except Exception as e:
        print(f"Auth Error (Local Decode): {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Paths to data (fallback for local development)
BASE_DIR = Path(__file__).parent.parent
JOBS_FILE = BASE_DIR / ".tmp" / "jobs_filtered.json"
PROFILE_FILE = BASE_DIR / ".tmp" / "user_profile.json"

@app.get("/")
def read_root():
    return {
        "status": "HyperApply API is running",
        "supabase_connected": supabase is not None
    }

@app.get("/api/jobs")
def get_jobs():
    if not JOBS_FILE.exists():
        # Return mock data if no file yet
        return [
            {
                "id": "1",
                "title": "Software Engineer",
                "company": "TechCorp Berlin",
                "location": "Berlin",
                "match_score": 92,
                "latitude": 52.5200,
                "longitude": 13.4050,
                "status": "new"
            },
            {
                "id": "2",
                "title": "Frontend Developer",
                "company": "Startup Munich",
                "location": "Munich",
                "match_score": 75,
                "latitude": 48.1351,
                "longitude": 11.5820,
                "status": "applied"
            }
        ]
    
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Add fake coordinates for the 3D map demo
    for job in data:
        if "latitude" not in job:
            job["latitude"] = 51.1657 + (random.random() - 0.5) * 4
            job["longitude"] = 10.4515 + (random.random() - 0.5) * 4
        
    return data

@app.get("/api/profile/skills")
def get_skills():
    if not PROFILE_FILE.exists():
        return []
        
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        profile = json.load(f)
        
    # Transform profile skills into Skill Tree format
    skills_list = []
    raw_skills = profile.get("skills", [])
    
    if isinstance(raw_skills, list):
        for skill in raw_skills:
            if isinstance(skill, str):
                skills_list.append({
                    "name": skill,
                    "level": random.randint(60, 95),
                    "category": "Detected",
                    "required_for": random.randint(3, 15)
                })
    
    return skills_list

# Auto-extraction background task for certificates
async def auto_extract_certificate(document_id: str, user_id: str, content_text: str):
    """
    Background task to automatically extract certificate data after upload.
    Runs asynchronously without blocking the upload response.
    Tracks status: pending → processing → done/failed
    """
    try:
        print(f"🤖 Auto-extracting certificate {document_id}...")
        
        # Update status to 'processing'
        supabase.table("documents")\
            .update({"analysis_status": "processing"})\
            .eq("id", document_id)\
            .execute()
        
        # Get user's API key
        profile_res = supabase.table("profiles")\
            .select("openrouter_key")\
            .eq("id", user_id)\
            .execute()
        
        if not profile_res.data or not profile_res.data[0].get("openrouter_key"):
            error_msg = "No OpenRouter API key configured"
            print(f"⚠️ {error_msg} for user {user_id}")
            supabase.table("documents")\
                .update({
                    "analysis_status": "failed",
                    "analysis_error": error_msg
                })\
                .eq("id", document_id)\
                .execute()
            return
        
        # Decrypt API key
        from services.encryption import decrypt_value
        api_key = decrypt_value(profile_res.data[0]["openrouter_key"])
        
        # Extract certificate data using LLM
        from services.llm import extract_certificate_data
        from services.dedup import generate_certificate_fingerprint
        
        extracted_data = extract_certificate_data(content_text, api_key)
        
        # Generate fingerprint for deduplication
        fingerprint = generate_certificate_fingerprint(extracted_data)
        
        # Check for duplicates
        existing_res = supabase.table("certificate_structured_data")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("fingerprint", fingerprint)\
            .execute()
        
        if existing_res.data:
            print(f"⚠️ Duplicate certificate detected (fingerprint: {fingerprint})")
            # Delete the duplicate document
            supabase.table("documents").delete().eq("id", document_id).execute()
            return
        
        # Save structured data
        supabase.table("certificate_structured_data").insert({
            "user_id": user_id,
            "document_id": document_id,
            "parsed_data": extracted_data,
            "original_ocr_data": extracted_data,
            "fingerprint": fingerprint
        }).execute()
        
        # Update status to 'done'
        supabase.table("documents")\
            .update({
                "analysis_status": "done",
                "analyzed_at": datetime.utcnow().isoformat()
            })\
            .eq("id", document_id)\
            .execute()
        
        print(f"✅ Auto-extracted certificate: {extracted_data.get('title', 'Unknown')}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Auto-extraction failed for {document_id}: {error_msg}")
        traceback.print_exc()
        
        # Update status to 'failed'
        supabase.table("documents")\
            .update({
                "analysis_status": "failed",
                "analysis_error": error_msg[:500]  # Truncate long errors
            })\
            .eq("id", document_id)\
            .execute()


# File Upload with Supabase Storage (Authenticated)
@app.post("/api/upload/{type}")
async def upload_file(
    type: str, 
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    user: dict = Depends(get_current_user)
):
    if not supabase:
        raise HTTPException(
            status_code=503,
            detail="Supabase not configured. Add SUPABASE_URL and SUPABASE_SERVICE_KEY to backend/.env"
        )
    
    if type not in ["cv", "certificate", "experience"]:
        raise HTTPException(status_code=400, detail="Invalid upload type")
    
    try:
        user_id = user.id
        print(f"Authenticated Upload for User ID: {user_id}")

        # Read file content
        file_content = await file.read()
        
        # Generate storage path: <user_id>/<type>/<timestamp>_<filename>
        # Organizing by user_id folder is good practice for RLS (even if bucket is flat)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        storage_path = f"{type}/{timestamp}_{file.filename}"
        
        # Upload to Supabase Storage
        print(f"Uploading to Supabase: {storage_path}")
        storage_response = supabase.storage.from_("documents").upload(
            storage_path,
            file_content,
            {"content-type": file.content_type}
        )
        
        # Get public URL (optional, for later retrieval)
        public_url = supabase.storage.from_("documents").get_public_url(storage_path)
        
        # Insert into documents table
        document_data = {
            "user_id": user_id,
            "doc_type": type,
            "original_filename": file.filename,
            "storage_path": storage_path,
            "mime_type": file.content_type
        }
        
        # Set initial analysis status for certificates
        if type == "certificate":
            document_data["analysis_status"] = "pending"



        # PHASE 4: Extract Text for CVs
        if type == "cv":
            # Define log file path relative to this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(base_dir, "parsing_log.txt")
            
            try:
                print(f"Parsing CV text for {file.filename}...")
                content_text = parse_cv(file_content, file.filename)
                
                # Log success/failure to file for visibility
                with open(log_path, "a", encoding="utf-8") as f:
                    if content_text:
                        msg = f"✅ Extracted {len(content_text)} chars from {file.filename}"
                        document_data["content_text"] = content_text
                    else:
                        msg = f"⚠️ No text extracted from {file.filename} (empty result)"
                    f.write(msg + "\n")
                
                print(msg)

            except Exception as e:
                err_msg = f"❌ CV Parsing Failed: {e}"
                print(err_msg)
                # Try to log error, but don't crash upload if log fails
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(err_msg + "\n")
                except:
                    pass

        # PHASE 4 Step 4: Certificate OCR
        elif type == "certificate":
            try:
                from services.certificate_parser import parse_certificate
                print(f"Running OCR for certificate {file.filename}...")
                
                # Use the same file_content read earlier
                parsing_result = parse_certificate(file_content, file.filename)
                
                extracted_text = parsing_result.get("text", "")
                method = parsing_result.get("method", "unknown")
                
                if extracted_text:
                    print(f"✅ Certificate OCR Success ({method}): {len(extracted_text)} chars")
                    document_data["content_text"] = extracted_text
                else:
                    print(f"⚠️ Certificate OCR produced no text. Error: {parsing_result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Certificate Parsing Failed: {e}")





        
        print(f"Inserting document record: {document_data}")
        # Insert using service role (admin) to bypass RLS for metadata creation
        # (Since the user is already verified via JWT)
        db_response = supabase.table("documents").insert(document_data).execute()
        
        doc_id = db_response.data[0]["id"]
        
        # Trigger auto-extraction for certificates with OCR text
        if type == "certificate" and document_data.get("content_text") and background_tasks:
            background_tasks.add_task(
                auto_extract_certificate,
                document_id=doc_id,
                user_id=user.id,
                content_text=document_data["content_text"]
            )
            print(f"🚀 Queued auto-extraction for certificate {doc_id}")
        
        return {
            "filename": file.filename,
            "status": "uploaded",
            "type": type,
            "document_id": doc_id,
            "storage_path": storage_path,
            "public_url": public_url,
            "user_id": user_id
        }
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Upload failed: {e}")
        print(error_trace)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/api/health/uploads")
def check_upload_health():
    if not supabase:
        return {
            "status": "error",
            "error": "Supabase not configured",
            "supabase_url": SUPABASE_URL,
            "has_key": bool(SUPABASE_KEY)
        }
    
    try:
        # Test Supabase connection
        buckets = supabase.storage.list_buckets()
        return {
            "status": "ok",
            "supabase_connected": True,
            "storage_buckets": [b.name for b in buckets]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# ... existing code ...

# Import LLM Service
try:
    from services.llm import extract_resume_data
except ImportError:
    # Fallback if running from root directory
    from backend.services.llm import extract_resume_data

# ... existing code ...

# ... imports ...
try:
    from utils.encryption import encrypt_value, decrypt_value
    from services.cv_parser import parse_cv
except ImportError:
    from backend.utils.encryption import encrypt_value, decrypt_value
    from backend.services.cv_parser import parse_cv

# ... existing code ...

class APIKeyRequest(BaseModel):
    key: str

@app.get("/api/settings/get-key-status")
async def get_key_status(user: dict = Depends(get_current_user)):
    try:
        profile_res = supabase.table("profiles").select("openrouter_key").eq("id", user.id).single().execute()
        if profile_res.data and profile_res.data.get("openrouter_key"):
            return {"has_key": True, "masked": "********"}
        return {"has_key": False}
    except Exception as e:
        print(f"Status Check Error: {e}")
        return {"has_key": False}

@app.post("/api/settings/save-key")
async def save_api_key(
    request: APIKeyRequest,
    user: dict = Depends(get_current_user)
):
    key = request.key
    if not key or not key.startswith("sk-or-"):
         raise HTTPException(status_code=400, detail="Invalid API Key format (must start with sk-or-)")
    
    try:
        # Encrypt before saving
        encrypted_key = encrypt_value(key)
        
        # Update Profile
        supabase.table("profiles").update({"openrouter_key": encrypted_key}).eq("id", user.id).execute()
        
        return {"status": "success", "message": "Key encrypted and saved."}
    except Exception as e:
        print(f"Save Key Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save key securely.")

@app.get("/api/debug-status")
async def debug_db_statuses():
    try:
        from main import supabase
        res = supabase.table("jobs").select("status").limit(50).execute()
        valid = list(set([x.get("status") for x in res.data if x.get("status")]))
        return {"status": "success", "db_statuses": valid}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ... extract_cv_data update ...

@app.post("/api/cv/extract/{document_id}")
async def extract_cv_data(
    document_id: str, 
    user: dict = Depends(get_current_user)
):
    """
    Extracts structured data from a CV using OpenRouter/LLM.
    Requires 'content_text' to be present in the document.
    """
    print(f"🚀 Starting extraction for doc: {document_id}")

    # 1. Get Encrypted Key
    try:
        profile_res = supabase.table("profiles").select("openrouter_key").eq("id", user.id).single().execute()
        
        if not profile_res.data or not profile_res.data.get("openrouter_key"):
             raise HTTPException(status_code=400, detail="OpenRouter API Key not found. Please add it in Settings.")
        
        encrypted_key = profile_res.data["openrouter_key"]
        api_key = decrypt_value(encrypted_key)
        
    except Exception as e:
        print(f"Profile Fetch/Decrypt Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve API Key settings")

    # 2. Get Document Content (Text)
    try:
        # Fetch metadata directly
        doc_res = supabase.table("documents").select("content_text, original_filename").eq("id", document_id).eq("user_id", user.id).single().execute()
        
        if not doc_res.data:
             raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_res.data
        content_text = document.get("content_text")
        
        if not content_text:
             raise HTTPException(status_code=400, detail="Document has no text content. Was it parsed correctly?")

        print(f"📄 Found content for {document.get('original_filename')} ({len(content_text)} chars)")
             
    except Exception as e:
         print(f"Document Fetch Error: {e}")
         raise HTTPException(status_code=500, detail="Failed to read document metadata")

    # 3. Call LLM Service
    try:
        extracted_data = extract_resume_data(content_text, api_key)
        print("✅ LLM Extraction Successful")
        
        # 4. Store in Database
        # Upsert into cv_structured_data
        structured_record = {
            "user_id": user.id,
            "document_id": document_id,
            "parsed_data": extracted_data,
            "original_ai_data": extracted_data, # ✨ Save original AI version
            "updated_at": "now()"
        }
        
        # We need to check if it exists or use upsert. 
        # The schema has UNIQUE(document_id), so upsert works.
        supabase.table("cv_structured_data").upsert(structured_record, on_conflict="document_id").execute()
        print("💾 Saved to cv_structured_data (with AI version)")

        return {
            "status": "success",
            "data": extracted_data
        }
    except Exception as e:
        print(f"LLM Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Extraction Failed: {str(e)}")


@app.put("/api/cv/update/{document_id}")
async def update_cv_data(
    document_id: str, 
    updated_data: dict,
    user: dict = Depends(get_current_user)
):
    """
    Updates the structured data for a CV (User edits).
    Does NOT overwrite 'original_ai_data'.
    """
    try:
        # Validate ownership first
        # (Although RLS handles this, explicit check gives better error messages)
        existing = supabase.table("cv_structured_data").select("user_id").eq("document_id", document_id).single().execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="CV Data not found")
        
        if existing.data["user_id"] != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this CV")

        # Update parsed_data only
        update_payload = {
            "parsed_data": updated_data,
            "updated_at": "now()"
        }
        
        res = supabase.table("cv_structured_data").update(update_payload).eq("document_id", document_id).execute()
        
        return {"status": "success", "message": "CV updated successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Update Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update CV data")


@app.get("/api/me/cv")
async def get_my_cv(user: dict = Depends(get_current_user)):
    """
    Get the latest CV for the current user and its extracted data.
    """
    try:
        # 1. Get latest CV document
        doc_res = supabase.table("documents")\
            .select("id, original_filename, content_text, created_at, storage_path")\
            .eq("user_id", user.id)\
            .eq("doc_type", "cv")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
            
        if not doc_res.data:
            return {"found": False}
        
        doc = doc_res.data[0]
        
        # 2. Get structured data if exists
        struct_res = supabase.table("cv_structured_data")\
            .select("parsed_data, updated_at")\
            .eq("document_id", doc["id"])\
            .execute()
            
        parsed_data = struct_res.data[0]["parsed_data"] if struct_res.data else None
        
        return {
            "found": True,
            "document_id": doc["id"],
            "filename": doc["original_filename"],
            "created_at": doc["created_at"],
            "has_text": bool(doc["content_text"]),
            "parsed_data": parsed_data
        }
    except Exception as e:
        print(f"Error fetching CV: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch CV data")


# ============================================
# CERTIFICATE ENDPOINTS
# ============================================

@app.post("/api/certificate/extract/{document_id}")
async def extract_certificate_data(
    document_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Extracts structured data from a certificate using OpenRouter/LLM.
    Requires 'content_text' (OCR result) to be present in the document.
    """
    print(f"🎓 Starting certificate extraction for doc: {document_id}")

    # 1. Get Encrypted Key
    try:
        profile_res = supabase.table("profiles").select("openrouter_key").eq("id", user.id).single().execute()
        
        if not profile_res.data or not profile_res.data.get("openrouter_key"):
             raise HTTPException(status_code=400, detail="OpenRouter API Key not found. Please add it in Settings.")
        
        encrypted_key = profile_res.data["openrouter_key"]
        api_key = decrypt_value(encrypted_key)
        
    except Exception as e:
        print(f"Profile Fetch/Decrypt Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve API Key settings")

    # 2. Get Document Content (OCR Text)
    try:
        doc_res = supabase.table("documents").select("content_text, original_filename").eq("id", document_id).eq("user_id", user.id).single().execute()
        
        if not doc_res.data:
             raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_res.data
        content_text = document.get("content_text")
        
        if not content_text:
             raise HTTPException(status_code=400, detail="Document has no OCR text. Was it processed correctly?")

        print(f"📄 Found OCR content for {document.get('original_filename')} ({len(content_text)} chars)")
             
    except Exception as e:
         print(f"Document Fetch Error: {e}")
         raise HTTPException(status_code=500, detail="Failed to read document metadata")

    # 3. Call LLM Service for Certificate Extraction
    try:
        from services.llm import extract_certificate_data as llm_extract_cert
        from schemas.certificate import CertificateSchema
        
        extracted_data = llm_extract_cert(content_text, api_key)
        print("✅ LLM Certificate Extraction Successful")
        
        # 4. Store in Database
        structured_record = {
            "user_id": user.id,
            "document_id": document_id,
            "parsed_data": extracted_data,
            "original_ocr_data": extracted_data,  # Save original AI version
            "updated_at": "now()"
        }
        
        supabase.table("certificate_structured_data").upsert(structured_record, on_conflict="document_id").execute()
        print("💾 Saved to certificate_structured_data")

        return {
            "status": "success",
            "data": extracted_data
        }
    except Exception as e:
        print(f"LLM Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Extraction Failed: {str(e)}")


@app.get("/api/me/certificate-insights")
async def get_certificate_insights(user: dict = Depends(get_current_user)):
    """
    Get aggregated certificate insights with deduplicated skills and status.
    Returns analysis-first view data with processing status for each certificate.
    """
    try:
        # Get all certificate documents with status
        docs_res = supabase.table("documents")\
            .select("id, analysis_status, analysis_error, analyzed_at")\
            .eq("user_id", user.id)\
            .eq("doc_type", "certificate")\
            .order("created_at", desc=True)\
            .execute()
        
        # Get all certificate structured data
        certs_res = supabase.table("certificate_structured_data")\
            .select("document_id, parsed_data, created_at")\
            .eq("user_id", user.id)\
            .order("created_at", desc=True)\
            .execute()
        
        if not docs_res.data:
            return {"certificates": [], "unique_skills": [], "total_count": 0}
        
        # Create lookup for structured data by document_id
        structured_data_map = {
            cert["document_id"]: cert["parsed_data"] 
            for cert in certs_res.data
        } if certs_res.data else {}
        
        # Build certificates list with status
        certificates = []
        all_skills = []
        
        for doc in docs_res.data:
            doc_id = doc["id"]
            parsed_data = structured_data_map.get(doc_id)
            
            cert_info = {
                "document_id": doc_id,
                "status": doc["analysis_status"],
                "error": doc.get("analysis_error"),
                "analyzed_at": doc.get("analyzed_at")
            }
            
            if parsed_data:
                cert_info.update(parsed_data)
                # Collect skills
                skills = parsed_data.get("skills", [])
                if skills:
                    all_skills.extend(skills)
            
            certificates.append(cert_info)
        
        # Deduplicate skills (case-insensitive)
        from services.dedup import deduplicate_skills
        unique_skills = deduplicate_skills(all_skills)
        
        return {
            "certificates": certificates,
            "unique_skills": unique_skills,
            "total_count": len(certificates)
        }
    except Exception as e:
        print(f"Error fetching insights: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch insights")


@app.post("/api/certificate/retry/{document_id}")
async def retry_certificate_analysis(
    document_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    Retry failed certificate analysis.
    Resets status to pending and triggers auto-extraction again.
    """
    try:
        # Verify document belongs to user and is a certificate
        doc_res = supabase.table("documents")\
            .select("id, content_text, doc_type")\
            .eq("id", document_id)\
            .eq("user_id", user.id)\
            .eq("doc_type", "certificate")\
            .single()\
            .execute()
        
        if not doc_res.data:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        content_text = doc_res.data.get("content_text")
        if not content_text:
            raise HTTPException(status_code=400, detail="No OCR text available for analysis")
        
        # Reset status to pending
        supabase.table("documents")\
            .update({
                "analysis_status": "pending",
                "analysis_error": None
            })\
            .eq("id", document_id)\
            .execute()
        
        # Trigger auto-extraction
        background_tasks.add_task(
            auto_extract_certificate,
            document_id=document_id,
            user_id=user.id,
            content_text=content_text
        )
        
        return {"status": "retry_queued", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrying certificate: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retry analysis")



@app.get("/api/me/certificates")
async def get_my_certificates(user: dict = Depends(get_current_user)):
    """
    Get all certificates for the current user with their extracted data.
    Returns array of certificate objects.
    """
    try:
        # Fetch all certificate documents for user
        docs_res = supabase.table("documents")\
            .select("id, original_filename, content_text, created_at, storage_path")\
            .eq("user_id", user.id)\
            .eq("doc_type", "certificate")\
            .order("created_at", desc=True)\
            .execute()
            
        if not docs_res.data:
            return {"certificates": []}
        
        certificates = []
        
        for doc in docs_res.data:
            # Get structured data if exists
            struct_res = supabase.table("certificate_structured_data")\
                .select("parsed_data, updated_at")\
                .eq("document_id", doc["id"])\
                .execute()
                
            parsed_data = struct_res.data[0]["parsed_data"] if struct_res.data else None
            
            certificates.append({
                "document_id": doc["id"],
                "filename": doc["original_filename"],
                "created_at": doc["created_at"],
                "has_text": bool(doc["content_text"]),
                "parsed_data": parsed_data,
                "storage_path": doc["storage_path"]
            })
        
        return {"certificates": certificates}
        
    except Exception as e:
        print(f"Error fetching certificates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch certificates")


# ============================================================================
# JOB MATCHING ENDPOINTS
# ============================================================================

class JobIngestRequest(BaseModel):
    url: str


@app.post("/api/jobs/ingest")
async def ingest_job(
    request: JobIngestRequest,
    user: dict = Depends(get_current_user)
):
    """
    Ingest a job from URL, apply filters, and calculate match score.
    """
    try:
        from services.job_scraper import ingest_job
        
        result = ingest_job(request.url, user.id, supabase)
        return result
        
    except Exception as e:
        print(f"Error ingesting job: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/matches")
async def get_job_matches(
    min_score: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """
    Get all jobs with match scores.
    Filter by minimum score and limit results.
    """
    try:
        query = supabase.table("jobs")\
            .select("*")\
            .eq("user_id", user.id)\
            .gte("match_score", min_score)\
            .order("match_score", desc=True)\
            .limit(limit)
        
        print(f"DEBUG: /api/jobs/matches | User: {user.id} | Min Score: {min_score}")
        
        # execution
        result = query.execute()
        jobs = result.data if result.data else []
        
        print(f"DEBUG: Found {len(jobs)} jobs matching criteria.")
        if jobs:
            print(f"DEBUG: EXISTING JOB STATUS EXAMPLE: {jobs[0].get('status')}")
        
        # Count filtered vs total
        total_res = supabase.table("jobs")\
            .select("id", count="exact")\
            .eq("user_id", user.id)\
            .execute()
            
        print(f"DEBUG: Total jobs in DB for user: {total_res.count}")
        
        filtered_res = supabase.table("jobs")\
            .select("id", count="exact")\
            .eq("user_id", user.id)\
            .eq("filtered_out", True)\
            .execute()
        
        return {
            "jobs": jobs,
            "total": total_res.count if total_res.count else 0,
            "filtered_count": filtered_res.count if filtered_res.count else 0,
            "debug_info": {
                "user_id": user.id,
                "min_score_param": min_score,
                "jobs_found_count": len(jobs),
                "total_in_db": total_res.count,
                "filtered_out_in_db": filtered_res.count
            }
        }
        
    except Exception as e:
        print(f"Error fetching job matches: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch job matches")


@app.get("/api/jobs/{job_id}/score")
async def get_job_score(
    job_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get detailed match report for a specific job.
    """
    try:
        result = supabase.table("jobs")\
            .select("*")\
            .eq("id", job_id)\
            .eq("user_id", user.id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = result.data
        
        return {
            "job_id": job["id"],
            "match_score": job["match_score"],
            "matched_skills": job["matched_skills"],
            "missing_skills": job["missing_skills"],
            "strengths_summary": job["strengths_summary"],
            "recommendation": "apply" if job["match_score"] >= 50 else "skip"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching job score: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch job score")

@app.post("/api/jobs/discover")
async def discover_jobs(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    Trigger automated job discovery.
    Runs as a background task to avoid blocking the UI.
    """

    try:
        from services.job_discovery import discover_and_score_jobs
        
        # Run in background to avoid blocking
        background_tasks.add_task(
            discover_and_score_jobs,
            user_id=user.id,
            supabase=supabase
        )
        
        return {"status": "discovery_started", "message": "Job discovery has been queued"}
        
    except Exception as e:
        print(f"Error starting job discovery: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to start job discovery")

@app.get("/api/linkedin/status")
async def get_linkedin_status(user: dict = Depends(get_current_user)):
    """Get the current status and rate limits of the LinkedIn Assistant."""
    import services.linkedin_assistant as la
    return {
        "status": "running" if la._browser_context else "idle",
        "applies_today": la._applies_today,
        "max_applies": 50
    }

@app.post("/api/linkedin/launch")
async def launch_linkedin(user: dict = Depends(get_current_user)):
    """Launch the assisted LinkedIn browser."""
    try:
        await launch_linkedin_browser()
        return {"status": "success", "message": "LinkedIn Assistant launched"}
    except Exception as e:
        import traceback
        print(f"Error launching LinkedIn: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/linkedin/stop")
async def stop_linkedin(user: dict = Depends(get_current_user)):
    """Stop the assisted LinkedIn browser."""
    try:
        await stop_linkedin_browser()
        return {"status": "success", "message": "LinkedIn Assistant stopped"}
    except Exception as e:
        print(f"Error stopping LinkedIn: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/linkedin/capture")
async def capture_linkedin(user: dict = Depends(get_current_user)):
    """Capture search results from the active LinkedIn tab."""
    try:
        result = await capture_current_search_results(user.id, supabase)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Capture failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error capturing LinkedIn jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/shortlist")
async def shortlist_job(
    job_id: str,
    user: dict = Depends(get_current_user)
):
    """Mark a job as shortlisted."""
    try:
        supabase.table("jobs").update({"status": "shortlisted"}).eq("id", job_id).eq("user_id", user.id).execute()
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        import traceback
        print(f"🔥 SHORTLIST DB ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/reject")
async def reject_job(
    job_id: str,
    user: dict = Depends(get_current_user)
):
    """Mark a job as rejected."""
    try:
        supabase.table("jobs").update({"status": "rejected"}).eq("id", job_id).eq("user_id", user.id).execute()
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/capture-details")
async def capture_details(
    job_id: str,
    user: dict = Depends(get_current_user)
):
    """Trigger detailed capture for a specific job."""
    try:
        from services.linkedin_assistant import capture_job_details
        result = await capture_job_details(job_id, user.id, supabase)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/linkedin/apply/{job_id}")
async def apply_linkedin(
    job_id: str,
    dry_run: bool = False,
    user: dict = Depends(get_current_user)
):
    """Trigger autofill for LinkedIn Easy Apply."""
    print(f"📥 [API] Received apply request for job: {job_id} (dry_run={dry_run})")
    try:
        from services.linkedin_assistant import autofill_easy_apply_modal
        result = await autofill_easy_apply_modal(job_id, user.id, supabase, dry_run=dry_run)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/linkedin/stop-actions")
async def stop_linkedin_actions(
    user: dict = Depends(get_current_user)
):
    """Signal the assistant to stop current automation."""
    try:
        from services.linkedin_assistant import request_stop
        request_stop()
        return {"status": "success", "message": "Stop requested."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# PHASE 9: CV TAILORING & COVER LETTER API
# ============================================

@app.get("/api/jobs/{job_id}/materials")
async def get_job_materials(job_id: str, user: dict = Depends(get_current_user)):
    try:
        cv_res = supabase.table("cv_versions").select("*").eq("job_id", job_id).eq("user_id", user.id).execute()
        
        # SAFER CHECK: Return 404 if no tailored CV exists yet
        if not cv_res.data or len(cv_res.data) == 0:
            return {"cv": None, "cover_letters": [], "message": "Please click 'Generate CV' first."}
        
        cl_res = supabase.table("cover_letters").select("*").eq("job_id", job_id).eq("user_id", user.id).execute()
        return {
            "cv": cv_res.data[0],
            "cover_letters": cl_res.data
        }
    except Exception as e:
        print(f"Materials Fetch Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch materials")

@app.post("/api/jobs/{job_id}/tailor-cv")
async def trigger_cv_tailoring(job_id: str, user: dict = Depends(get_current_user)):
    """Generate tailored CV JSON from latest profile data."""
    try:
        # 1. Get Job Description
        job = supabase.table("jobs").select("description").eq("id", job_id).single().execute()
        if not job.data: raise HTTPException(status_code=404, detail="Job not found")
        
        # 2. Get User Profile and Certs
        from services.job_matcher import get_user_skills
        user_skills = get_user_skills(supabase, user.id)
        
        # Get latest CV structured data
        cv_res = supabase.table("documents").select("id").eq("user_id", user.id).eq("doc_type", "cv").order("created_at", desc=True).limit(1).execute()
        if not cv_res.data: raise HTTPException(status_code=400, detail="No CV uploaded yet.")
        
        struct_res = supabase.table("cv_structured_data").select("parsed_data").eq("document_id", cv_res.data[0]["id"]).single().execute()
        if not struct_res.data: raise HTTPException(status_code=400, detail="CV not yet parsed. Please analyze it first.")
        
        # 3. Tailor
        tailored = tailor_cv(job.data['description'], struct_res.data['parsed_data'], user_skills)
        
        # 4. Upsert into cv_versions (JSON only for now, file generated on Save)
        record = {
            "user_id": user.id,
            "job_id": job_id,
            "tailored_content": tailored,
            "keywords_found": tailored['ats_metadata']['keywords_found'],
            "keywords_missing": tailored['ats_metadata']['keywords_missing'],
            "ats_score": int((len(tailored['ats_metadata']['keywords_found']) / max(1, len(tailored['ats_metadata']['keywords_found']) + len(tailored['ats_metadata']['keywords_missing']))) * 100)
        }
        
        supabase.table("cv_versions").upsert(record, on_conflict="user_id,job_id").execute()
        
        return {"status": "success", "data": record}
    except Exception as e:
        print(f"Tailoring Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/generate-cl")
async def trigger_cl_generation(job_id: str, variant: str = "professional", user: dict = Depends(get_current_user)):
    """Generate AI Cover Letter variant."""
    try:
        # Get Key
        profile_res = supabase.table("profiles").select("openrouter_key").eq("id", user.id).single().execute()
        if not profile_res.data or not profile_res.data.get("openrouter_key"):
             raise HTTPException(status_code=400, detail="OpenRouter API Key not found.")
        api_key = decrypt_value(profile_res.data["openrouter_key"])

        # Get JD
        job = supabase.table("jobs").select("description").eq("id", job_id).single().execute()
        
        # Get tailored CV or fallback to original
        tailored_res = supabase.table("cv_versions").select("tailored_content").eq("job_id", job_id).eq("user_id", user.id).execute()
        if tailored_res.data:
            cv_data = tailored_res.data[0]['tailored_content']
        else:
            # Fallback to latest parsed CV
            cv_res = supabase.table("documents").select("id").eq("user_id", user.id).eq("doc_type", "cv").order("created_at", desc=True).limit(1).execute()
            struct_res = supabase.table("cv_structured_data").select("parsed_data").eq("document_id", cv_res.data[0]["id"]).single().execute()
            cv_data = struct_res.data['parsed_data']

        # Generate
        content = generate_cover_letter(job.data['description'], cv_data, api_key, variant)
        
        # Upsert
        record = {
            "user_id": user.id,
            "job_id": job_id,
            "variant": variant,
            "content": content
        }
        supabase.table("cover_letters").upsert(record, on_conflict="user_id,job_id,variant").execute()
        
        return {"status": "success", "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/save-materials")
async def save_and_finalize_materials(job_id: str, user: dict = Depends(get_current_user)):
    """finalize CV/CL and generate docx files."""
    try:
        # 1. Fetch current data
        cv_res = supabase.table("cv_versions").select("*").eq("job_id", job_id).eq("user_id", user.id).single().execute()
        cl_res = supabase.table("cover_letters").select("*").eq("job_id", job_id).eq("user_id", user.id).execute()
        
        if not cv_res.data: raise HTTPException(status_code=404, detail="No tailored CV found to finalize.")

        # 2. Generate Docx Files locally first
        temp_dir = Path(".tmp/materials")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        cv_path = temp_dir / f"CV_{user.id}_{job_id}.docx"
        generate_cv_docx(cv_res.data['tailored_content'], str(cv_path))
        
        # Upload CV to storage
        storage_path = f"{user.id}/{job_id}/tailored_cv.docx"
        with open(cv_path, "rb") as f:
            supabase.storage.from_("materials").upload(storage_path, f, {"upsert": "true"})
            
        supabase.table("cv_versions").update({"storage_path": storage_path}).eq("id", cv_res.data['id']).execute()

        # Generate Cover Letters if they exist
        for cl in cl_res.data:
            cl_path = temp_dir / f"CL_{cl['variant']}_{user.id}_{job_id}.docx"
            generate_cover_letter_docx(cl['content'], cv_res.data['tailored_content'].get('full_name', 'User'), str(cl_path))
            
            cl_storage_path = f"{user.id}/{job_id}/cover_letter_{cl['variant']}.docx"
            with open(cl_path, "rb") as f:
                supabase.storage.from_("materials").upload(cl_storage_path, f, {"upsert": "true"})
            
            supabase.table("cover_letters").update({"storage_path": cl_storage_path}).eq("id", cl['id']).execute()

        return {"status": "success", "message": "Materials finalized and saved to storage."}
    except Exception as e:
        print(f"Finalization Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/linkedin/questions/submit")
async def submit_question_answer(
    data: dict,
    user: dict = Depends(get_current_user)
):
    """Save a new answer to the question bank."""
    try:
        # data expected: { "question_text": "...", "answer_text": "..." }
        update_data = {
            "user_id": user.id,
            "question_text": data["question_text"],
            "answer_text": data["answer_text"],
            "category": data.get("category", "general")
        }
        supabase.table("linkedin_question_bank").upsert(update_data, on_conflict="user_id,question_text").execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{job_id}/proof")
async def get_application_proof(job_id: str, user = Depends(get_current_user)):
    """Returns the success screenshot for an application if it exists."""
    proof_path = os.path.join(LOGS_DIR, job_id, "success_proof.png")
    if os.path.exists(proof_path):
        return FileResponse(proof_path)
    
    # Fallback: check if DB has a custom path
    res = supabase.table("applications").select("success_screenshot_path").eq("job_id", job_id).eq("user_id", user.id).single().execute()
    if res.data and res.data.get("success_screenshot_path"):
        db_path = res.data["success_screenshot_path"]
        if os.path.exists(db_path):
            return FileResponse(db_path)
            
    raise HTTPException(status_code=404, detail="Proof screenshot not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
