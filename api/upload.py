import os

from fastapi import APIRouter, File, UploadFile

from rag.rag_pipeline import process, records

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

current_doc_path = None

@router.post("/upload")
def upload_document(doc: UploadFile = File(...)):
    global current_doc_path
    path = os.path.join(UPLOAD_DIR, doc.filename)

    with open(path, "wb") as f:
        f.write(doc.file.read())

    existing = next((r for r in records if r["path"] == path), None)

    if existing:
        current_doc_path = path
        return {
            "filename": doc.filename,
            "message": "Document already processed.",
            "can_use_mic": True
        }

    process(path)
    current_doc_path = path
    return {
        "filename": doc.filename,
        "message": "Document uploaded and processed successfully.",
        "can_use_mic": True
    }
