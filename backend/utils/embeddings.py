import sys
import os
import uuid
from typing import List, Optional
from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone

load_dotenv()

# Ensure emoji-heavy print() works on Windows consoles
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Config ────────────────────────────────────────────────────────────────────
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME", "resume-index")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini's text-embedding-004 supports output_dimensionality.
# Our Pinecone index was created with 512 dimensions, so we match that.
EMBEDDING_DIMENSIONS = 512

# ── Gemini Client ─────────────────────────────────────────────────────────────
gemini_client: Optional[genai.Client] = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("[✅] Gemini client initialized.")
else:
    print("[⚠️] GEMINI_API_KEY not found. Embedding generation will fail.")

# ── Pinecone (lazy singleton) ─────────────────────────────────────────────────
_pinecone_index = None

def get_pinecone_index():
    """Lazily connect to Pinecone and return the index. Returns None on failure."""
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index

    if not PINECONE_API_KEY:
        print("[⚠️] PINECONE_API_KEY is not set.")
        return None

    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        existing_indexes = [idx.name for idx in pc.list_indexes()]

        if INDEX_NAME not in existing_indexes:
            print(f"[⚠️] Pinecone index '{INDEX_NAME}' does not exist.")
            return None

        _pinecone_index = pc.Index(INDEX_NAME)
        print(f"[✅] Connected to Pinecone index: {INDEX_NAME}")
        return _pinecone_index

    except Exception as e:
        print(f"[❌] Error connecting to Pinecone: {e}")
        return None


# ── Embedding Generation ──────────────────────────────────────────────────────
def generate_embeddings(text: str) -> List[float]:
    """
    Generates a 512-dimensional embedding for the given text using Google Gemini
    (text-embedding-004 with output_dimensionality=512 to match the Pinecone index).

    Args:
        text (str): The input text to embed.

    Returns:
        List[float]: A list of floats representing the embedding, or [] on failure.
    """
    if not text or not text.strip():
        print("[⚠️] Empty text passed to generate_embeddings. Skipping.")
        return []

    if not gemini_client:
        print("[❌] Gemini client not initialized. Check GEMINI_API_KEY.")
        return []

    try:
        response = gemini_client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config={"output_dimensionality": EMBEDDING_DIMENSIONS},
        )
        embedding = response.embeddings[0].values
        print(f"[✅] Generated Gemini embedding ({len(embedding)}-dim) for: '{text[:30]}...'")
        return list(embedding)
    except Exception as e:
        print(f"[❌] Error generating Gemini embedding: {e}")
        return []


# ── Store Embedding ───────────────────────────────────────────────────────────
def store_embedding(text: str, resume_id: int) -> int:
    """
    Stores or updates an embedding in Pinecone.
    Uses a deterministic vector ID ('resume_<id>') so Pinecone's native upsert
    handles deduplication — no need for a separate query-before-upsert.

    Args:
        text (str): The input text to embed and store.
        resume_id (int): The database ID of the resume.

    Returns:
        int: 1 on success, 0 on failure.
    """
    index = get_pinecone_index()
    if index is None:
        print("[⚠️] Pinecone index unavailable. Skipping storage.")
        return 0

    embedding = generate_embeddings(text)
    if not embedding:
        print("[⚠️] Failed to generate embedding. Skipping storage.")
        return 0

    try:
        # Deterministic ID: upsert will update if the vector already exists,
        # or insert if it's new — no pre-query needed.
        vector_id = f"resume_{resume_id}"
        index.upsert(vectors=[(vector_id, embedding, {"text": text, "id": str(resume_id)})])
        print(f"[✅] Upserted embedding in Pinecone with ID: {vector_id}")
        return 1
    except Exception as e:
        print(f"[❌] Error storing embedding in Pinecone: {e}")
        return 0


# ── Match Embeddings ──────────────────────────────────────────────────────────
def match_embeddings(user_embedding: List[float], top_k: int = 3) -> List[str]:
    """
    Matches the user_embedding against stored embeddings in Pinecone and returns
    the IDs of the top matches.

    Args:
        user_embedding (List[float]): The query embedding vector.
        top_k (int): Number of top matches to retrieve (default 3).

    Returns:
        List[str]: List of resume IDs (strings) for the top matches.
                   Returns an empty list if no matches found or on error.
    """
    index = get_pinecone_index()
    if index is None:
        print("[⚠️] Pinecone index not initialized. Skipping match.")
        return []

    if not user_embedding:
        print("[⚠️] Empty embedding passed to match_embeddings.")
        return []

    try:
        results = index.query(vector=user_embedding, top_k=top_k, include_metadata=True)

        if results and results.get("matches"):
            match_ids = [
                match["metadata"]["id"]
                for match in results["matches"]
                if "metadata" in match and "id" in match["metadata"]
            ]
            print(f"[✅] Top {top_k} Matches: {match_ids}")
            return match_ids

        print("[⚠️] No matches found in Pinecone.")
        return []

    except Exception as e:
        print(f"[❌] Error matching embeddings: {e}")
        return []
