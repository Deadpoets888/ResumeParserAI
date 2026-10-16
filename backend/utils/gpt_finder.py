import os
import json
from google import genai
from typing import List, Dict, Any, Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def extract_prompt_info(description: str) -> Dict[str, Any]:
    print("Generating information based on user prompt")
    prompt = f"""Extract relevant resume details from the given user description. 
The user may provide explicit or implicit information about their skills, work experience, education, certifications, projects, or GPA.

Extract and classify the following fields:
- Skills: Includes programming languages, frameworks, libraries, tools, technologies, methodologies, and relevant technical or domain-specific expertise.
- Work Experience: Job roles, companies, internships, or professional experiences.
- Education: Degrees, institutions, and areas of study.
- Certifications: Any relevant certifications or professional qualifications.
- Projects: Names or descriptions of personal, academic, or professional projects.
- GPA: If mentioned, extract it; otherwise, return "0".

If a field is not mentioned, return it as an empty list.
    
    User Prompt:
    {description}
    
    Return ONLY raw JSON (no markdown, no code fences, no explanation). Example format:
    {{"Skills": [], "Work_experience": [], "Education": [], "Certifications": [], "Projects": [], "Gpa": "0"}}
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "system_instruction": "You are an expert in analyzing user descriptions to extract resume-related information. Return ONLY raw JSON.",
            "temperature": 0,
        }
    )
    
    raw = response.text.strip()
    # Strip markdown code fences if Gemini wraps anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    print(raw)

    try:
        resume_info = json.loads(raw) if raw.startswith("{") else {}
    except (json.JSONDecodeError, Exception):
        resume_info = {}
    
    return {
        "skills": resume_info.get("Skills", []),
        "work_experience": resume_info.get("Work_experience", []),
        "education": resume_info.get("Education", []),
        "certifications": resume_info.get("Certifications", []),
        "projects": resume_info.get("Projects", []),
        "gpa": resume_info.get("Gpa", "0")
    }