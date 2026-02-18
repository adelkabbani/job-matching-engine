
from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    location: Optional[str] = None

class ExperienceItem(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None  # "Present" or date
    description: Optional[str] = None
    technologies: List[str] = []

class EducationItem(BaseModel):
    institution: str
    degree: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    link: Optional[str] = None

class ResumeSchema(BaseModel):
    contact_info: ContactInfo
    summary: Optional[str] = None
    skills: List[str] = []
    experience: List[ExperienceItem] = []
    education: List[EducationItem] = []
    projects: List[ProjectItem] = []
    certifications: List[str] = []
    data_quality_score: int = 0  # 0-100 score of how well data was extracted
    languages: List[str] = []
