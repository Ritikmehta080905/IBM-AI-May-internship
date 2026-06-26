# AI Lecture Voice-to-Notes Generator Backend

## Overview

This FastAPI backend supports lecture audio upload, transcription, summarization, quiz generation, and flashcards.

## Setup

1. Create a Python virtual environment:
   ```powershell
   cd "c:\PROJECT\IBM AI\backend"
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Create an `.env` file from `.env.example`, set your valid OpenAI API key, and ensure storage paths are correct.

> Note: This app now requires a real OpenAI API key for all AI operations. There is no local fallback.

4. Run the app:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- `POST /api/auth/register` - register user
- `POST /api/auth/token` - login
- `GET /api/auth/me` - retrieve current user profile
- `POST /api/upload` - upload audio lecture
- `POST /api/transcribe/{lecture_id}` - transcribe lecture
- `POST /api/summary/{lecture_id}` - generate notes
- `POST /api/quiz/{lecture_id}` - generate quiz
- `POST /api/flashcards/{lecture_id}` - generate flashcards
- `GET /api/history` - list user's lectures
- `GET /api/lecture/{lecture_id}` - get lecture details and generated content
- `GET /api/lecture/{lecture_id}/transcript` - fetch the lecture transcript
- `GET /api/lecture/{lecture_id}/notes` - fetch generated lecture notes
- `GET /api/lecture/{lecture_id}/quiz` - fetch quiz items for a lecture
- `GET /api/lecture/{lecture_id}/flashcards` - fetch flashcards for a lecture
- `GET /api/search?q=<query>` - search lecture transcripts
- `POST /api/chat` - chat with lecture content

## Example Usage

Register a user:
```powershell
curl -X POST "http://127.0.0.1:8000/api/auth/register" -H "Content-Type: application/json" -d "{\"name\": \"Test User\", \"email\": \"test@example.com\", \"password\": \"TestPassword123\"}"
```

Login and retrieve token:
```powershell
curl -X POST "http://127.0.0.1:8000/api/auth/token" -H "Content-Type: application/x-www-form-urlencoded" -d "username=test@example.com&password=TestPassword123"
```

Upload audio:
```powershell
curl -X POST "http://127.0.0.1:8000/api/upload" -H "Authorization: Bearer <token>" -F "file=@lecture.mp3"
```

## Notes

- The project uses SQLite for local development and OpenAI APIs for transcription and generation.
- You must provide `OPENAI_API_KEY` in `.env` for AI calls to work. This app requires a real OpenAI key; there is no local fallback.
- The `JWT_SECRET_KEY` should be changed in production to a strong, random secret.

## Frontend

A lightweight static frontend is available in the `frontend` folder. To run it locally:
```powershell
cd "c:\PROJECT\IBM AI\frontend"
python -m http.server 5500
```
Then open `http://127.0.0.1:5500` in your browser.

## Testing

Run tests from the backend directory after installing dependencies:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
