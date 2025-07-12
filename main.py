import os

import google.generativeai as genai
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.transcribe import router as transcribe_router
from api.upload import router as upload_router

app = FastAPI()

# CORS Middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register API routers
app.include_router(upload_router)
app.include_router(transcribe_router)

if __name__ == "__main__":
    # running the app on local host
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)