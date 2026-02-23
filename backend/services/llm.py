
import requests
import json
import os
from typing import Dict, Any, Optional

try:
    from schemas.resume import ResumeSchema
except ImportError:
    from backend.schemas.resume import ResumeSchema

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Using Gemini 2.0 Flash as it is fast, cheap/free, and great at JSON
DEFAULT_MODEL = "google/gemini-2.0-flash-001" 

def extract_resume_data(text_content: str, api_key: str) -> Dict[str, Any]:
    """
    Extracts structured data from resume text using OpenRouter LLM.
    Enforces ResumeSchema structure.
    Implements 1 retry on failure.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "HyperApply",
        "Content-Type": "application/json"
    }
    
    # Get the strict JSON schema
    schema_json = json.dumps(ResumeSchema.model_json_schema(), indent=2)
    
    system_prompt = f"""
    You are an expert Resume Parser. Your job is to extract structured data from the provided CV text.
    
    STRICT OUTPUT RULES:
    1. You must return ONLY valid JSON.
    2. The JSON must strictly adhere to the following schema:
    {schema_json}
    
    3. Do not include markdown formatting (like ```json ... ```) in the response. Just the raw JSON string.
    4. If a field is not found, leave it null or empty list as per schema default.
    5. Clean up any weird character artifacts from the text.
    """

    user_prompt = f"Here is the CV text:\n\n{text_content[:20000]}" # Truncate if too huge to avoid errors, though Flash has context.

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "response_format": { "type": "json_object" }
    }
    
    def call_llm(current_payload):
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=current_payload)
        
        if response.status_code != 200:
            error_msg = f"OpenRouter API Error {response.status_code}: {response.text}"
            print(error_msg)
            raise Exception(error_msg)

        result = response.json()
        if 'choices' not in result or len(result['choices']) == 0:
             raise Exception("Invalid response from OpenRouter (no choices)")

        content = result['choices'][0]['message']['content']
        
        # Cleanup markdown if present
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
            content = content.replace("```", "")
            
        return content.strip()

    # Attempt 1
    try:
        print(f"🤖 Calling LLM ({DEFAULT_MODEL})...")
        json_str = call_llm(payload)
        
        # Validate against Pydantic
        # This ensures the output matches our schema types exactly
        parsed_data = ResumeSchema.model_validate_json(json_str)
        print("✅ LLM Output Validated against Schema.")
        return parsed_data.model_dump(mode='json')

    except Exception as e:
        print(f"⚠️ Attempt 1 Failed: {e}")
        
        # Attempt 2: Retry with error message
        print("🔄 Retrying with correction prompt...")
        
        retry_prompt = f"""
        The previous attempt to parse the CV failed. 
        Please try again and ensure the output is STRICT VALID JSON matching the schema provided.
        Error encountered: {str(e)}
        """
        
        payload["messages"].append({"role": "user", "content": retry_prompt})
        
        try:
            json_str = call_llm(payload)
            parsed_data = ResumeSchema.model_validate_json(json_str)
            print("✅ Attempt 2 Successful.")
            return parsed_data.model_dump(mode='json')
            
        except Exception as e2:
            print(f"❌ Extraction Failed after retry: {e2}")
            raise Exception(f"AI Extraction Failed: {str(e2)}")

def extract_certificate_data(ocr_text: str, api_key: str) -> Dict[str, Any]:
    """
    Extracts structured data from certificate OCR text using OpenRouter LLM.
    Enforces CertificateSchema structure.
    Implements 1 retry on failure.
    """
    try:
        from schemas.certificate import CertificateSchema
    except ImportError:
        from backend.schemas.certificate import CertificateSchema
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "HyperApply",
        "Content-Type": "application/json"
    }
    
    # Get the strict JSON schema
    schema_json = json.dumps(CertificateSchema.model_json_schema(), indent=2)
    
    system_prompt = f"""
    You are an expert Certificate Parser. Your job is to extract structured data from OCR text of certificates.
    
    STRICT OUTPUT RULES:
    1. You must return ONLY valid JSON.
    2. The JSON must strictly adhere to the following schema:
    {schema_json}
    
    3. Do not include markdown formatting (like ```json ... ```) in the response. Just the raw JSON string.
    4. If a field is not found in the text, leave it null or empty list as per schema default.
    5. For the 'title' field, extract the certificate name, course name, or achievement title.
    6. For the 'issuer' field, extract the organization, institution, or company name.
    7. For 'completion_date', extract any date mentioned (flexible format: YYYY-MM-DD, Month Year, etc.).
    8. For 'skills', extract relevant keywords, technologies, or competencies mentioned.
    9. Set 'confidence' to 'high' if all fields are clearly found, 'medium' if some are inferred, 'low' if mostly guessing.
    """

    user_prompt = f"Here is the certificate OCR text:\n\n{ocr_text[:10000]}"  # Truncate if too long

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    def call_llm(current_payload):
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=current_payload)
        
        if response.status_code != 200:
            error_msg = f"OpenRouter API Error {response.status_code}: {response.text}"
            print(error_msg)
            raise Exception(error_msg)

        result = response.json()
        if 'choices' not in result or len(result['choices']) == 0:
             raise Exception("Invalid response from OpenRouter (no choices)")

        content = result['choices'][0]['message']['content']
        
        # Cleanup markdown if present
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
            content = content.replace("```", "")
            
        return content.strip()
    
    # Attempt 1
    try:
        json_str = call_llm(payload)
        parsed_data = CertificateSchema.model_validate_json(json_str)
        print("✅ Certificate Extraction Successful (Attempt 1)")
        return parsed_data.model_dump(mode='json')
        
    except Exception as e:
        print(f"⚠️ Attempt 1 Failed: {e}")
        
        # Retry with clarification
        retry_prompt = f"""
        The previous response was invalid. Please try again.
        Remember:
        - Return ONLY raw JSON (no markdown, no extra text)
        - Follow the schema exactly
        - Use null for missing fields
        
        Certificate OCR text:
        {ocr_text[:10000]}
        """
        
        payload["messages"].append({"role": "user", "content": retry_prompt})
        
        try:
            json_str = call_llm(payload)
            parsed_data = CertificateSchema.model_validate_json(json_str)
            print("✅ Certificate Extraction Successful (Attempt 2)")
            return parsed_data.model_dump(mode='json')
            
        except Exception as e2:
            print(f"❌ Certificate Extraction Failed after retry: {e2}")
            raise Exception(f"AI Certificate Extraction Failed: {str(e2)}")

def test_connection(api_key: str):
    """
    Verifies the OpenRouter API connection with a simple prompt.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "HyperApply",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "user", "content": "Say 'Connection Verified' if you can hear me."}
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Status {response.status_code}: {response.text}"
            }
            
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return {
                "success": True,
                "message": result['choices'][0]['message']['content']
            }
        
        return {"success": False, "error": "Invalid response format"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_cover_letter(
    job_description: str,
    cv_data: Dict,
    api_key: str,
    variant: str = "professional"
) -> str:
    """
    Generates a tailored cover letter using the LLM.
    Variants: 'professional', 'concise'.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "HyperApply",
        "Content-Type": "application/json"
    }

    style_guide = "Professional, slightly formal, and authoritative." if variant == "professional" \
                  else "Concise, direct, and punchy. Focus on key impact."

    system_prompt = f"""
    You are an expert Career Coach. Your job is to write a high-converting cover letter.
    
    FACTUAL RULES:
    1. NEVER invent experience, companies, or dates.
    2. Use the provided CV data as the ONLY source of truth.
    3. Match existing skills from the CV to the Job Description.

    STYLE RULES:
    - Variant Style: {style_guide}
    - Tone: Confident but humble.
    - Format: Standard business letter format (without headers/footers, just the body).
    - Length: Under 350 words.
    """

    user_prompt = f"""
    Job Description:
    {{job_description[:5000]}}

    Tailored CV Data:
    {{json.dumps(cv_data, indent=2)[:5000]}}

    Write the cover letter now. Response should be ONLY the letter text.
    """

    payload = {{
        "model": DEFAULT_MODEL,
        "messages": [
            {{"role": "system", "content": system_prompt}},
            {{"role": "user", "content": user_prompt}}
        ],
        "temperature": 0.7
    }}

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Cover Letter Generation Error: {e}")
        raise Exception(f"Failed to generate cover letter: {str(e)}")

def generate_search_keywords(profile_data: Dict, api_key: str) -> list[str]:
    """
    Generates tailored LinkedIn search queries based on the user profile.
    Returns a list of 5-10 optimized search strings.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "HyperApply",
        "Content-Type": "application/json"
    }

    skills = profile_data.get("skills", [])
    experience_level = profile_data.get("experience_level", "Entry Level")
    
    # Extract locations from preferences or default to Berlin as per directive
    prefs = profile_data.get("preferences", {})
    locations = prefs.get("desired_locations", ["Berlin"])
    location_str = " or ".join(locations)

    system_prompt = """
    You are an expert Technical Recruiter and Boolean Search Master.
    Your goal is to generate high-precision LinkedIn search queries for a candidate.
    
    RULES:
    1. Focus on the candidate's STRONGEST skills.
    2. Combine Role + Skill + Location + Language (if implicit).
    3. Target the specific Experience Level requesting (Entry Level / Junior).
    4. Return ONLY a raw JSON array of strings. No markdown.
    5. Generate 5-10 distinct queries.
    
    Example Output:
    ["Junior Python Developer Berlin", "Entry Level React Engineer Berlin English", ...]
    """

    user_prompt = f"""
    Candidate Profile:
    Skills: {', '.join(skills[:20])} ...
    Experience Level: {experience_level}
    Target Location: {location_str}
    
    Generate the search queries now.
    """

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Cleanup markdown
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
            content = content.replace("```", "")
            
        return json.loads(content)
        
    except Exception as e:
        print(f"Keyword Generation Error: {e}")
        # Fallback
        return [f"Junior {s} Developer Berlin" for s in skills[:3]]

