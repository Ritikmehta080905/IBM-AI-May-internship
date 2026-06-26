import os


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


import uuid


def test_upload_requires_available_file(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    email = f"testuser+{uuid.uuid4().hex}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "TestPassword123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", b"not an audio file", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_get_lecture_detail_returns_uploaded_lecture(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    email = f"testuser+{uuid.uuid4().hex}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "TestPassword123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    upload_response = client.post(
        "/api/upload",
        files={"file": ("lecture.mp3", b"fake audio data", "audio/mpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_response.status_code == 200
    lecture_id = upload_response.json()["lecture_id"]

    detail_response = client.get(
        f"/api/lecture/{lecture_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["id"] == lecture_id
    assert payload["status"] == "uploaded"
    assert payload["file_name"] == "lecture.mp3"


def test_quiz_and_flashcards_can_be_retrieved(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    def fake_transcribe_audio(file_path: str) -> str:
        return "This is a sample lecture transcript for testing."

    def fake_generate_quiz(transcript: str, *args, **kwargs):
        return [
            {
                "question": "What is the sample topic?",
                "option_a": "Test",
                "option_b": "Example",
                "option_c": "Transcript",
                "option_d": "Lecture",
                "answer": "Lecture",
            }
        ]

    def fake_generate_flashcards(transcript: str):
        return [
            {"question": "What does the transcript describe?", "answer": "A sample lecture."}
        ]

    def fake_generate_summary(transcript: str):
        return {"summary": "Sample lecture summary.", "key_points": "Point A, Point B"}

    import app.utils.openai_client as openai_client
    import app.utils.vector_store as vector_store
    import app.routes.lecture as lecture_routes

    monkeypatch.setattr(openai_client, "transcribe_audio", fake_transcribe_audio)
    monkeypatch.setattr(openai_client, "generate_summary", fake_generate_summary)
    monkeypatch.setattr(openai_client, "generate_quiz", fake_generate_quiz)
    monkeypatch.setattr(openai_client, "generate_flashcards", fake_generate_flashcards)
    monkeypatch.setattr(vector_store, "_compute_embedding", lambda text: [0.0] * 1536)
    monkeypatch.setattr(lecture_routes.vector_store, "_compute_embedding", lambda text: [0.0] * 1536)

    email = f"testuser+{uuid.uuid4().hex}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "TestPassword123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    upload_response = client.post(
        "/api/upload",
        files={"file": ("lecture.mp3", b"fake audio data", "audio/mpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_response.status_code == 200
    lecture_id = upload_response.json()["lecture_id"]

    transcribe_response = client.post(
        f"/api/transcribe/{lecture_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert transcribe_response.status_code == 200

    quiz_response = client.post(
        f"/api/quiz/{lecture_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert quiz_response.status_code == 200
    assert quiz_response.json()["quiz_count"] == 1

    flashcard_response = client.post(
        f"/api/flashcards/{lecture_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert flashcard_response.status_code == 200
    assert flashcard_response.json()["flashcard_count"] == 1

    quiz_list_response = client.get(
        f"/api/lecture/{lecture_id}/quiz",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert quiz_list_response.status_code == 200
    assert len(quiz_list_response.json()) == 1
    assert quiz_list_response.json()[0]["question"] == "What is the sample topic?"

    flashcard_list_response = client.get(
        f"/api/lecture/{lecture_id}/flashcards",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert flashcard_list_response.status_code == 200
    assert len(flashcard_list_response.json()) == 1
    assert flashcard_list_response.json()[0]["answer"] == "A sample lecture."

    notes_response = client.post(
        f"/api/summary/{lecture_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert notes_response.status_code == 200
    assert notes_response.json()["summary"] == "Sample lecture summary."

    transcript_response = client.get(
        f"/api/lecture/{lecture_id}/transcript",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert transcript_response.status_code == 200
    assert transcript_response.json()["transcript"] == "This is a sample lecture transcript for testing."

    notes_get_response = client.get(
        f"/api/lecture/{lecture_id}/notes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert notes_get_response.status_code == 200
    assert notes_get_response.json()["summary"] == "Sample lecture summary."
    assert "Point A" in notes_get_response.json()["key_points"]


def test_search_lectures_filters_by_transcript(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    def fake_transcribe_audio(file_path: str) -> str:
        return "This lecture covers Python testing and FastAPI development."

    import app.utils.openai_client as openai_client
    import app.utils.vector_store as vector_store
    import app.routes.lecture as lecture_routes
    monkeypatch.setattr(openai_client, "transcribe_audio", fake_transcribe_audio)
    monkeypatch.setattr(vector_store, "_compute_embedding", lambda text: [0.0] * 1536)
    monkeypatch.setattr(lecture_routes.vector_store, "_compute_embedding", lambda text: [0.0] * 1536)

    email = f"testuser+{uuid.uuid4().hex}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "TestPassword123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    upload_response = client.post(
        "/api/upload",
        files={"file": ("lecture.mp3", b"fake audio data", "audio/mpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_response.status_code == 200
    lecture_id = upload_response.json()["lecture_id"]

    transcribe_response = client.post(
        f"/api/transcribe/{lecture_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert transcribe_response.status_code == 200

    search_response = client.get(
        "/api/search?q=FastAPI",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert search_response.status_code == 200
    assert len(search_response.json()) == 1
    assert search_response.json()[0]["id"] == lecture_id


def test_chat_about_lecture_returns_answer(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    def fake_transcribe_audio(file_path: str) -> str:
        return "The lecture transcript explains how to build APIs with FastAPI."

    def fake_answer_question(question: str, context: str) -> str:
        return "It explains how to build APIs with FastAPI."

    import app.utils.openai_client as openai_client
    import app.utils.vector_store as vector_store
    import app.routes.lecture as lecture_routes
    monkeypatch.setattr(openai_client, "transcribe_audio", fake_transcribe_audio)
    monkeypatch.setattr(vector_store, "_compute_embedding", lambda text: [0.0] * 1536)
    monkeypatch.setattr(lecture_routes.vector_store, "_compute_embedding", lambda text: [0.0] * 1536)
    monkeypatch.setattr(openai_client, "answer_question", fake_answer_question)

    email = f"testuser+{uuid.uuid4().hex}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "TestPassword123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    upload_response = client.post(
        "/api/upload",
        files={"file": ("lecture.mp3", b"fake audio data", "audio/mpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_response.status_code == 200
    lecture_id = upload_response.json()["lecture_id"]

    transcribe_response = client.post(
        f"/api/transcribe/{lecture_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert transcribe_response.status_code == 200

    chat_response = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What does the lecture explain?", "lecture_id": lecture_id},
    )
    assert chat_response.status_code == 200
    assert chat_response.json()["answer"] == "It explains how to build APIs with FastAPI."
