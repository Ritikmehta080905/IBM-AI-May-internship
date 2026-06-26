# AI Lecture Voice-to-Notes

This repository contains a FastAPI backend and a lightweight static frontend for an AI-powered lecture voice-to-notes generator.

## Folders

- `backend/` - FastAPI app, SQLite storage, OpenAI integration, JWT auth, and pytest tests.
- `frontend/` - Static HTML/CSS/JS UI for interacting with the backend.

## Setup

1. Backend
   ```powershell
   cd "c:\PROJECT\IBM AI\backend"
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   copy .env.example .env
   # then edit .env to set OPENAI_API_KEY and optionally JWT_SECRET_KEY
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Frontend
   ```powershell
   cd "c:\PROJECT\IBM AI\frontend"
   python -m http.server 5500
   ```

3. Open in browser
   `http://127.0.0.1:5500`

## Testing

Run backend tests:
```powershell
cd "c:\PROJECT\IBM AI\backend"
.\.venv\Scripts\python.exe -m pytest -q
```

## Docker

A complete end-to-end Docker setup is included.

1. Copy `.env.example` to `.env` and configure `OPENAI_API_KEY`.
2. Run:
   ```powershell
   docker compose up --build
   ```
3. Open the frontend:
   `http://127.0.0.1:5500`
4. Backend API is available at:
   `http://127.0.0.1:8000`

## Notes

- The backend requires a valid OpenAI API key.
- The app now includes semantic search and retrieval-augmented chat over lecture content.
- The frontend stores the JWT token locally in the browser.
- Audio upload supports `.mp3`, `.wav`, and `.m4a`.
