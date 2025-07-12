import os

from fastapi import APIRouter

from rag.rag_constants import ID_KEY
from rag.rag_pipeline import process, records
from rag.retriever_setup import vectorstore
from transcribe import transcribe_user_question
from utils.gemini import answer_with_gemini

router = APIRouter()
from api.upload import current_doc_path


@router.post("/transcribe")
def transcribe_and_answer():
    if not current_doc_path or not os.path.exists(current_doc_path):
        return {"error": "No document uploaded. Please upload a document first."}

    question = transcribe_user_question()
    print(f"🎤Transcribed Question: {question}")

    existing = next((r for r in records if r["path"] == current_doc_path), None)
    if not existing:
        print("⚠️ Not found in records. Re-processing.")
        process(current_doc_path)
        existing = next((r for r in records if r["path"] == current_doc_path), None)

    docs = vectorstore.similarity_search(
        question, k=3, filter={ID_KEY: existing["doc_id"]}
    )
    chunks = [doc.page_content for doc in docs]
    answer = answer_with_gemini(question, chunks)

    return {
        "question": question,
        "answer": answer
    }
