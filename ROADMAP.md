# ResumeParserAI: Learning & Modernization Roadmap

> **Status:** Phase 1 (Fixing Backend Bugs & Understanding the Data Pipeline) — In Progress  
> **Goal:** Step-by-step interactive learning journey

---

## 🧭 Project Purpose & Architecture
**ResumeParserAI** is an intelligent candidate screening application.
- **Frontend ([frontend/](frontend/)):** React interface for resume upload & semantic query search.
- **Backend ([backend/](backend/)):** FastAPI service orchestrating PDF extraction, AI parsing, and search logic.
- **AI Extraction ([backend/utils/](backend/utils/)):** PyMuPDF + OpenAI GPT-4 / Mistral OCR converts raw PDF resumes into structured JSON (skills, experience, education, GPA).
- **PostgreSQL:** Stores structured relational candidate records.
- **Pinecone:** Stores mathematical vector embeddings of resumes to power semantic natural language search.

---

## 🐛 Identified Bugs to Fix Step-by-Step (Phase 1)
1. **Pinecone API Key Name Discrepancy ([backend/utils/embeddings.py](backend/utils/embeddings.py:L8))**
2. **Windows Path Incompatibility ([backend/routes/resume.py](backend/routes/resume.py:L238))**
3. **FastAPI Background Tasks DB Session Bug ([backend/routes/resume.py](backend/routes/resume.py:L283))**
4. **Dangerous `eval()` ([backend/utils/gpt_finder.py](backend/utils/gpt_finder.py:L42))**
5. **GPA Float Casting Crash ([backend/routes/resume.py](backend/routes/resume.py:L414))**
6. **API Call in Loop Waste ([backend/routes/resume.py](backend/routes/resume.py:L365))**
7. **Leftover Template Code Cleanups ([backend/routes/resume.py](backend/routes/resume.py))**

---

## 🎨 UI Modernization Plan (Phase 2 & Phase 3)
1. **Modern Layout & Design System:**
   - Dark/glassmorphic theme, sleek typography (Google Fonts - Inter/Plus Jakarta Sans), micro-animations, gradient accents.
2. **Interactive Upload Experience:**
   - Drag-and-drop PDF dropzone, model selector (GPT-4 vs Mistral) with visual comparison cards, live progress state.
3. **Multi-Candidate Search & Dashboard:**
   - Search bar with natural language prompt hints.
   - Ranked candidate cards showing Match Score percentage, highlight badges for matched skills, expandable work history, and contact quick-links.


