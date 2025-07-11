import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# configure gemini with credentials
def configure_gemini():
    api_key = os.getenv("GEMINI_IMAGE_API_KEY")
    assert api_key, "GEMINI_IMAGE_API_KEY not set"
    genai.configure(api_key=api_key)

# answer generation
def answer_with_gemini(question: str, context_chunks: list) -> str:
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite-preview-06-17")
        context = "\n\n".join(context_chunks)
        prompt = f"""You are an assistant helping with document analysis.

            Use the context provided below to answer the user question.
        
            Context:
            {context}
        
            Question: {question}
        
            Answer the question accurately and concisely based only on the context."""
            
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini error: {e}"