import fitz  # PyMuPDF for PDF text extraction
import json
import os
from google import genai

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing Gemini API key. Set 'GEMINI_API_KEY' in the environment.")

client = genai.Client(api_key=GEMINI_API_KEY)
print("[INFO] Gemini client initialized successfully.")

def extract_resume_data_and_structure(pdf_path):
    """Extracts text from a PDF resume and processes it with Gemini Flash to return structured JSON."""
    
    try:

        # Extract text from the PDF
        print(f"[INFO] Extracting text from PDF: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
            extracted_text = "\n".join(page.get_text("text") for page in doc)
        except Exception as e:
            raise RuntimeError(f"Error reading PDF file: {str(e)}")
        
        if not extracted_text.strip():
            raise ValueError("Extracted text is empty. Ensure the PDF contains selectable text.")

        print("[INFO] Successfully extracted text from PDF.")

        # Define the prompt
        prompt = f"""
        Extract the following details from this resume and return ONLY valid JSON (no markdown, no code fences):
        - Name
        - Email
        - Phone Number
        - Skills
        - Work Experience (Company, Role, Duration)
        - Education (Degree, Institution, Year)
        - Certifications
        - Projects
        - Gpa

        Resume Text:
        {extracted_text}
        """

        print("[INFO] Sending extracted text to Gemini Flash for processing...")

        # Call Gemini Flash
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "system_instruction": "You extract structured information from resumes and return ONLY raw JSON with no markdown or code fences.",
                    "temperature": 0,
                }
            )
        except Exception as e:
            raise RuntimeError(f"Error calling Gemini API: {str(e)}")

        print("[INFO] Received response from Gemini Flash.")

        # Parse JSON response
        try:
            raw = response.text.strip()
            # Strip markdown code fences if Gemini wraps anyway
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            structured_data = json.loads(raw.strip())
            print("[INFO] Successfully parsed structured data.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON. Error: {str(e)}\nRaw: {response.text[:300]}")

        return structured_data

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {"error": str(e)}
