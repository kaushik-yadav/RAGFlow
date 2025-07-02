import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from transcribe import transcribe_user_question

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/transcribe")
def get_transcription():
    text = transcribe_user_question()
    return {"question": text}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
