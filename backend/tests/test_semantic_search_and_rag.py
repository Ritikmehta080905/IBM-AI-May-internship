import uuid


def test_semantic_search_returns_matching_lecture(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    def fake_transcribe_audio(file_path: str) -> str:
        return "This lecture covers semantic search and retrieval augmented generation."

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

    monkeypatch.setattr(vector_store, "find_lecture_ids_for_query", lambda query, user_id, n_results=10: [lecture_id])

    transcribe_response = client.post(
        f"/api/transcribe/{lecture_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert transcribe_response.status_code == 200

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
        "/api/search/semantic?q=semantic",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["query"] == "semantic"
    assert payload["results"] and payload["results"][0]["id"] == lecture_id


def test_chat_with_rag_uses_retrieval_context(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    def fake_transcribe_audio(file_path: str) -> str:
        return "This lecture explains semantic search and retrieval augmented generation."

    def fake_answer_question_with_context(question: str, context: str) -> str:
        return "It uses lecture excerpts to answer the question."

    import app.utils.openai_client as openai_client
    import app.utils.vector_store as vector_store
    import app.routes.lecture as lecture_routes

    monkeypatch.setattr(openai_client, "transcribe_audio", fake_transcribe_audio)
    monkeypatch.setattr(openai_client, "answer_question_with_context", fake_answer_question_with_context)
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

    monkeypatch.setattr(
        vector_store,
        "search_relevant_chunks",
        lambda query, user_id, lecture_id=None, n_results=3: [
            {"lecture_id": lecture_id or 1, "chunk_index": 0, "excerpt": "Sample excerpt for RAG.", "score": 0.01}
        ],
    )

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
        json={"question": "How is RAG used?", "lecture_id": lecture_id, "use_rag": True},
    )
    assert chat_response.status_code == 200
    payload = chat_response.json()
    assert payload["answer"] == "It uses lecture excerpts to answer the question."
    assert payload["sources"] == [f"Lecture {lecture_id} chunk 0"]
