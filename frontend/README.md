# AI Lecture Voice-to-Notes Frontend

This is a lightweight static frontend for the AI lecture backend.

## Setup

1. Start the backend app:
   ```powershell
   cd "c:\PROJECT\IBM AI\backend"
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Serve the frontend from the `frontend` folder:
   ```powershell
   cd "c:\PROJECT\IBM AI\frontend"
   python -m http.server 5500
   ```

3. Open the frontend in your browser:
   ```text
   http://127.0.0.1:5500
   ```

## Usage

- Register or login to obtain a JWT.
- Upload lecture audio via `POST /api/upload`.
- Use the lecture ID to transcribe, summarize, generate quiz/flashcards, and fetch generated content.
- Use the search box to query existing transcripts.
- Use the chat box to ask a question about the selected lecture.

## Notes

- The backend already allows CORS for all origins, so the frontend can request the API from `http://localhost:5500`.
- The frontend stores the authentication token in browser local storage.
