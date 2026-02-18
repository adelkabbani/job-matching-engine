from pydantic import BaseModel, Field
from typing import Optional, List

class CertificateSchema(BaseModel):
    """Structured certificate data extracted from OCR text"""
    title: str = Field(description="Certificate title or course name")
    issuer: str = Field(description="Issuing organization or institution")
    completion_date: Optional[str] = Field(None, description="Date of completion (flexible format: YYYY-MM-DD, Month Year, etc.)")
    skills: List[str] = Field(default_factory=list, description="Identified skills, technologies, or keywords from certificate")
    confidence: Optional[str] = Field(None, description="Extraction confidence level: high, medium, low")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Advanced Python Programming",
                "issuer": "Coursera",
                "completion_date": "2024-01-15",
                "skills": ["Python", "Data Structures", "Algorithms", "Object-Oriented Programming"],
                "confidence": "high"
            }
        }
