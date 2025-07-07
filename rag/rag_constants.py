import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GEMINI_IMAGE_API_KEY = os.getenv("GEMINI_IMAGE_API_KEY")

COLLECTION_NAME = 'multi_modal_rag'
ID_KEY = 'doc_id'
PROCESSED_FILE = 'processed.json'
MAX_DOCS = 5

assert GROQ_API_KEY, 'Set GROQ_API_KEY in .env'
assert COHERE_API_KEY, 'Set COHERE_API_KEY in .env'