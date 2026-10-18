from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, JSON, Text, Float
from database import Base

class Resume(Base):
    __tablename__ = "resume"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=True)
    skills = Column(JSON, nullable=False)  # Dict[str, Any]
    work_experience = Column(JSON, nullable=True)  # List[Dict[str, Any]]
    education = Column(JSON, nullable=False)  # List[Dict[str, Any]]
    certifications = Column(JSON, nullable=True)  # List[Dict[str, Any]]
    projects = Column(JSON, nullable=False)  # List[Dict[str, Any]]
    gpa = Column(String, nullable=True, default="0")
    model_type = Column(String, nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    
    resumes = relationship("Resume", back_populates="user")