from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks, File, UploadFile, Form
from sqlalchemy.orm import Session 
from typing import Dict,Any
from database import get_db
import shutil
from schemas import ResumeResponse
from enum import Enum
import os
from utils.gpt_fitz import extract_resume_data_and_structure as gpt_fitz_extractor
from utils.mistral import extract_and_structure_resume as mistral_extractor
from models import Resume 
from schemas import SearchRequest, ResumeCreate
from utils.embeddings import generate_embeddings,store_embedding,match_embeddings
from utils.gpt_finder import extract_prompt_info
import time

router = APIRouter()

@router.get("/resume/{resume_id}", response_model=ResumeResponse)
def get_travel_resume(resume_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a travel resume by its ID.
    """
    try:
        print(f"Fetching travel resume with ID: {resume_id}")
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume:
            print(f"resume with ID {resume_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Travel resume not found"
            )
        
        print(f"Successfully retrieved resume: {resume.id}")
        return resume
    except Exception as e:
        print(f"Error retrieving resume with ID {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve travel resume: {str(e)}"
        )

def store_resume_data(extracted_data: dict, db: Session):
    """
    Stores or updates the extracted resume data in the database.

    Args:
        extracted_data (dict): Parsed resume details.
        db (Session): Database session.

    Returns:
        int: The stored or updated resume entry ID.
    """
    try:
        # Check if a record with the given email already exists
        existing_entry = db.query(Resume).filter_by(email=extracted_data.get("Email")).first()

        if existing_entry:
            # Update existing entry
            existing_entry.name = extracted_data.get("Name", existing_entry.name)
            existing_entry.phone_number = extracted_data.get("Phone Number", existing_entry.phone_number)
            existing_entry.skills = extracted_data.get("Skills", existing_entry.skills)
            existing_entry.work_experience = extracted_data.get("Work Experience", existing_entry.work_experience)
            existing_entry.education = extracted_data.get("Education", existing_entry.education)
            existing_entry.certifications = extracted_data.get("Certifications", existing_entry.certifications)
            existing_entry.projects = extracted_data.get("Projects", existing_entry.projects)
            existing_entry.gpa = extracted_data.get("Gpa", existing_entry.gpa)
            existing_entry.model_type = extracted_data.get("model_type", existing_entry.model_type)

            db.commit()
            db.refresh(existing_entry)
            print("Existing resume entry updated successfully with ID:", existing_entry.id)
            return existing_entry.id
        else:
            # Create a new entry
            resume_entry = Resume(
                name=extracted_data.get("Name"),
                email=extracted_data.get("Email"),
                phone_number=extracted_data.get("Phone Number"),
                skills=extracted_data.get("Skills"),
                work_experience=extracted_data.get("Work Experience"),
                education=extracted_data.get("Education"),
                certifications=extracted_data.get("Certifications"),
                projects=extracted_data.get("Projects"),
                gpa=extracted_data.get("Gpa"),
                model_type=extracted_data.get("model_type")
            )

            db.add(resume_entry)
            db.commit()
            db.refresh(resume_entry)
            print("New resume entry added successfully with ID:", resume_entry.id)
            return resume_entry.id
    except Exception as e:
        db.rollback()
        print(f"Error storing resume data: {str(e)}")
        return None


def extract_resume_data(pdf_path: str, model_type: str):
    """
    Extracts resume data based on the selected model type.

    Args:
        pdf_path (str): Path to the PDF resume.
        model_type (str): Model to use ('gpt_fitz' or 'mistral').

    Returns:
        dict: Extracted resume data.
    """
    print("model type :" ,model_type)
    if model_type == "gpt_fitz":
        return gpt_fitz_extractor(pdf_path)  # Calls function from gpt_fitz.py
    elif model_type == "mistral":
        return mistral_extractor(pdf_path)  # Calls function from mistral.py
    else:
        raise ValueError(f"Invalid model type: {model_type}. Choose 'gpt_fitz' or 'mistral'.")
    

def _delete_resume_from_db(resume_id: str, db: Session):
    """
    Deletes the resume from the database if embedding storage fails.
    
    Args:
        resume_id (str): Unique ID of the travel resume.
        db (Session): Database session.
    """
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            db.delete(resume)
            db.commit()
            print(f"[🗑️] resume ID {resume_id} removed from database due to embedding failure.")
        else:
            print(f"[⚠️] resume ID {resume_id} not found in database.")
    except Exception as e:
        print(f"[❌] Error removing resume from database: {e}")
        db.rollback()  # Ensure rollback in case of error
        
    
def _store_resume_embedding(resume_description: str, resume_id: int, db: Session) -> bool:
    """
    Generate and store an embedding for a resume description.
    
    Args:
        resume_description (str): The resume description.
        resume_id (str): Unique ID for the resume.
        db (Session): Database session.

    Returns:
        bool: True if successful, False otherwise.
    """
    print(f"Starting embedding storage for resume ID: {resume_id}")
    start_time = time.time()

    try:
        result = store_embedding(resume_description, resume_id)  # resume_id is already a string
        
        if result == 1:
            time_taken = time.time() - start_time
            print(f"[✅] Embedding stored successfully in {time_taken:.2f} seconds.")
            return True
        else:
            print("[❌] Failed to store embedding. Removing resume from DB...")
            _delete_resume_from_db(resume_id, db)
            return False
    except Exception as e:
        print(f"[❌] Error during embedding storage: {e}")
        _delete_resume_from_db(resume_id, db)
        return False
    
def _prepare_generation_text(data: dict) -> str:
    """
    Prepare a formatted text for resume data.
    
    Args:
        data: Resume data dictionary
    
    Returns:
        Formatted string for resume generation
    """
    print("Preparing text for resume generation")
    
    # Handle cases where any expected list is None
    skills = data.get('Skills', []) or []
    work_experience = data.get('Work Experience', data.get('Work_experience', [])) or []
    education = data.get('Education', []) or []
    certifications = data.get('Certifications', []) or []
    projects = data.get('Projects', []) or []
    
    # Format work experience details
    work_experience_str = "\n    ".join([
        f"{exp.get('Position', '')} at {exp.get('Company', '')} ({exp.get('Duration', '')}) - {exp.get('Description', '')}"
        for exp in work_experience
    ])
    
    # Format education details
    education_str = "\n    ".join([
        f"{edu.get('Degree', '')} from {edu.get('Institution', '')} ({edu.get('Year', '')})"
        for edu in education
    ])
    
    # Format certifications
    certifications_str = ", ".join(certifications)
    
    # Format projects
    projects_str = "\n    ".join([
        f"{proj.get('Name', '')}: {proj.get('Description', '')}"
        for proj in projects
    ])
    
    # Build the formatted text
    formatted_text = f"""
    Name: {data.get('Name', '')}
    Email: {data.get('Email', '')}
    Phone: {data.get('Phone_number', '')}
    
    Skills: {', '.join(skills)}
    
    Work Experience:
    {work_experience_str}
    
    Education:
    {education_str}
    
    Certifications: {certifications_str}
    
    Projects:
    {projects_str}
    
    GPA: {data.get('Gpa', '')}
    """.strip()
    
    return formatted_text
    

UPLOAD_DIR = "uploads"  # Folder to store uploaded PDFs
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def _process_resume_extraction(file_path: str, db: Session, model_type: str):
    """Background task to process the uploaded resume and extract data."""
    try:
        # Call your function to extract structured data from the PDF
        print("Extracting information from pdf")
        extracted_data = extract_resume_data(file_path,model_type)
        extracted_data['model_type']=model_type

        # TODO: Save extracted_data into database using `db`
        print("Extracted Data Successfully")  # Debugging

        print("Saving extracted data in the database table")
        id=store_resume_data(extracted_data,db)

        formatted_text = _prepare_generation_text(extracted_data)

        _store_resume_embedding(formatted_text,id,db)

    except Exception as e:
        print(f"Error processing resume: {str(e)}")

    

@router.post("/resume/", response_model=Dict[str, Any])
async def upload_resume(
    model_type: str = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload a resume as a PDF file. The information will be extracted in the background.
    """
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"Received resume: {file.filename}, saved at {file_path}")

        # Process the resume in the background
        background_tasks.add_task(_process_resume_extraction, file_path, db, model_type)

        return {
            "status": "processing",
            "message": "Your resume is being processed. This may take a few moments."
        }
    
    except Exception as e:
        print(f"Error uploading resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {str(e)}"
        )
    

def get_travel_resume_by_id(db: Session, resume_id: int):
    """
    Fetches a resume from the database by ID.

    Parameters:
    - db (Session): SQLAlchemy database session.
    - resume_id (int): ID of the resume.

    Returns:
    - Resume: The matching travel resume object.
    """
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if resume:
            print(f"[✅] Found Travel resume of :({resume.id})")
            return resume
        else:
            print("[⚠️] No travel resume found for the given ID.")
            return None

    except Exception as e:
        print(f"[❌] Error fetching travel resume: {e}")
        return None


@router.post("/search-resume/")
async def process_resume_search_rag(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Process a resume search request and return the best matching resume.
    """

    try:
        # Generate embeddings from user prompt
        print(f"Generating embeddings from user prompt: {request.user_prompt}")
        user_embeddings = generate_embeddings(request.user_prompt)
        
        # Match embeddings against Pinecone database
        print("Comparing against pinecone database")
        matched_result_ids = match_embeddings(user_embeddings)
        
        if not matched_result_ids:
            print("No suitable matches found after tag matching")
            return {"message": "No suitable matches found for your preferences"}
        
        # Fetch all matched resumes from DB
        matched_resume = [get_travel_resume_by_id(db, match_id) for match_id in matched_result_ids]
        # Filter out any None results (IDs not found in DB)
        matched_resume = [r for r in matched_resume if r is not None]

        if not matched_resume:
            return {"message": "No suitable matches found for your preferences"}

        # Convert matched resumes to ResumeCreate objects
        resume_objects = []
        for resume in matched_resume:
            resume_data = {
                "name": resume.name,
                "email": resume.email,
                "phone_number": resume.phone_number,
                "skills": resume.skills,
                "work_experience": resume.work_experience,
                "education": resume.education,
                "certifications": resume.certifications,
                "projects": resume.projects,
                "gpa": resume.gpa,
                "model_type": resume.model_type
            }
            resume_objects.append(ResumeCreate(**resume_data))

        # Extract relevant info from user prompt (done once, outside the loop)
        extracted_prompt_info = extract_prompt_info(request.user_prompt)

        def _extract_values_from_field(field) -> list:
            """Flatten a field (dict, list of dicts, or list of strings) into a flat list of strings."""
            values = []
            if isinstance(field, dict):
                for v in field.values():
                    if isinstance(v, list):
                        values.extend([str(x).lower() for x in v])
                    else:
                        values.append(str(v).lower())
            elif isinstance(field, list):
                for item in field:
                    if isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, list):
                                values.extend([str(x).lower() for x in v])
                            else:
                                values.append(str(v).lower())
                    else:
                        values.append(str(item).lower())
            return values

        # Score each resume against the extracted prompt info
        print("Scoring resumes against the user prompt")
        matching_resumes = []
        for resume in resume_objects:
            match_score = 0

            # Skills matching
            if extracted_prompt_info.get("skills") and resume.skills:
                prompt_skills = [s.lower() for s in extracted_prompt_info["skills"]]
                resume_skills = _extract_values_from_field(resume.skills)
                match_score += len(set(prompt_skills) & set(resume_skills))

            # Work experience matching
            if extracted_prompt_info.get("work_experience") and resume.work_experience:
                prompt_we = [s.lower() for s in extracted_prompt_info["work_experience"]]
                resume_we = _extract_values_from_field(resume.work_experience)
                match_score += len(set(prompt_we) & set(resume_we))

            # Education matching
            if extracted_prompt_info.get("education") and resume.education:
                prompt_edu = [s.lower() for s in extracted_prompt_info["education"]]
                resume_edu = _extract_values_from_field(resume.education)
                match_score += len(set(prompt_edu) & set(resume_edu))

            # Certifications matching
            if extracted_prompt_info.get("certifications") and resume.certifications:
                prompt_cert = [s.lower() for s in extracted_prompt_info["certifications"]]
                resume_cert = _extract_values_from_field(resume.certifications)
                match_score += len(set(prompt_cert) & set(resume_cert))

            # Projects matching
            if extracted_prompt_info.get("projects") and resume.projects:
                prompt_proj = [s.lower() for s in extracted_prompt_info["projects"]]
                resume_proj = _extract_values_from_field(resume.projects)
                match_score += len(set(prompt_proj) & set(resume_proj))

            # GPA matching (use float to handle values like "3.8")
            if extracted_prompt_info.get("gpa") and resume.gpa:
                try:
                    prompt_gpa = float(extracted_prompt_info["gpa"])
                    resume_gpa = float(resume.gpa)
                    match_score += 1 if resume_gpa >= prompt_gpa else 0
                except (ValueError, TypeError):
                    pass  # Ignore GPA comparison if conversion fails

            print(f"match_score for {resume.name}: {match_score}")
            matching_resumes.append((match_score, resume))

        # Sort resumes by highest match score
        matching_resumes.sort(reverse=True, key=lambda x: x[0])

        # Return best-matching resume
        best_match = matching_resumes[0][1]
        print(f"Best matching resume -> name: {best_match.name}, email: {best_match.email}")
        return best_match
        
    except Exception as e:
        print(f"Error processing search request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing search request: {str(e)}"
        )




'''@router.post("/search-resume/")
async def search_resume(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Search for resume based on user criteria and preferences.
    Results are emailed to the user as a PDF.
    """
    try:
        print(f"Received search request for tour from email")
        
        # Add the search processing to background tasks
        background_tasks.add_task(_process_resume_search_rag, request, db)
        
        return {
            "status": "processing",
            "message": "Your search is being processed. Results will be emailed to you shortly."
        }
    except Exception as e:
        print(f"Error initiating resume search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate resume search: {str(e)}"
        ) '''