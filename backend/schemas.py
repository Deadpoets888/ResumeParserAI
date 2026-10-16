# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ResumeBase(BaseModel):
    name: str
    email: str
    phone_number: Optional[str]
    skills: Any
    work_experience: Optional[List[Dict[str, Any]]]
    education: List[Dict[str, Any]]
    certifications: Optional[List[Dict[str, Any]]]
    projects: Optional[List[Dict[str, Any]]]
    gpa: Optional[str]
    model_type : str

class ResumeCreate(ResumeBase):
    pass

class ResumeResponse(ResumeBase):
    id: int
    
    class Config:
        orm_mode = True

class SearchRequest(BaseModel):
    user_prompt: str



