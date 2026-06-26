import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, lecture
from app.database import engine, Base
from app.config import UPLOAD_DIR, TRANSCRIPT_DIR, NOTES_DIR, VECTOR_STORE_DIR

for directory in (UPLOAD_DIR, TRANSCRIPT_DIR, NOTES_DIR, VECTOR_STORE_DIR):
    os.makedirs(directory, exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Lecture Voice-to-Notes Generator",
    description="FastAPI backend for audio transcription, note generation, quizzes, flashcards, and study chat.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(lecture.router, prefix="/api", tags=["lectures"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "AI Lecture backend is running."}
