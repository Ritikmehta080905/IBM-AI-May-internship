import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
TRANSCRIPT_DIR = os.getenv("TRANSCRIPT_DIR", "transcripts")
NOTES_DIR = os.getenv("NOTES_DIR", "notes")
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a"}
ALLOWED_DOC_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "vector_store")

