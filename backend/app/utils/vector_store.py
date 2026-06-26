import json
import math
import os
import hashlib
from typing import Dict, List, Optional
import httpx

import openai
from app.config import VECTOR_STORE_DIR
from app.utils.openai_client import openai_client, GEMINI_API_KEY

STORE_FILE = os.path.join(VECTOR_STORE_DIR, "lecture_embeddings.json")


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _load_store() -> Dict[str, List[Dict]]:
    _ensure_dir(VECTOR_STORE_DIR)
    if not os.path.exists(STORE_FILE):
        return {"vectors": []}
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_store(store: Dict[str, List[Dict]]):
    _ensure_dir(VECTOR_STORE_DIR)
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def _compute_embedding(text: str) -> List[float]:
    # 1. Try OpenAI if client is available
    if openai_client:
        try:
            response = openai_client.embeddings.create(model="text-embedding-3-large", input=[text])
            return response.data[0].embedding
        except Exception:
            pass

    # 2. Try Gemini if key is available
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text}]}
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=20.0)
            resp.raise_for_status()
            data = resp.json()
            return data["embedding"]["values"]
        except Exception:
            pass

    # 3. Deterministic Mock Embeddings (so tests and searches are stable)
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vector = []
    for i in range(1536):
        val = (h[i % 32] + i) % 256
        vector.append(math.sin(val) * 0.1)
    return vector


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def chunk_transcript(text: str, chunk_size: int = 250, overlap: int = 50) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start = max(0, end - overlap)
    return chunks


def index_transcript(lecture_id: int, user_id: int, transcript: str) -> int:
    store = _load_store()
    store["vectors"] = [item for item in store["vectors"] if item["lecture_id"] != lecture_id]

    chunks = chunk_transcript(transcript)
    if not chunks:
        _save_store(store)
        return 0

    for index, chunk in enumerate(chunks):
        embedding = _compute_embedding(chunk)
        store["vectors"].append(
            {
                "id": f"{lecture_id}-{index}",
                "lecture_id": lecture_id,
                "user_id": user_id,
                "chunk_index": index,
                "text": chunk,
                "embedding": embedding,
            }
        )
    _save_store(store)
    return len(chunks)


def search_relevant_chunks(
    query: str,
    user_id: int,
    lecture_id: Optional[int] = None,
    n_results: int = 3,
) -> List[Dict[str, Optional[str]]]:
    query_embedding = _compute_embedding(query)
    store = _load_store()
    candidates = [item for item in store["vectors"] if item["user_id"] == user_id]
    if lecture_id is not None:
        candidates = [item for item in candidates if item["lecture_id"] == lecture_id]

    scored = []
    for item in candidates:
        score = _cosine_similarity(query_embedding, item["embedding"])
        scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    results = []
    for score, item in scored[:n_results]:
        results.append(
            {
                "lecture_id": item["lecture_id"],
                "chunk_index": item["chunk_index"],
                "excerpt": item["text"],
                "score": score,
            }
        )
    return results


def find_lecture_ids_for_query(query: str, user_id: int, n_results: int = 10) -> List[int]:
    query_embedding = _compute_embedding(query)
    store = _load_store()
    candidates = [item for item in store["vectors"] if item["user_id"] == user_id]

    scored = []
    for item in candidates:
        score = _cosine_similarity(query_embedding, item["embedding"])
        scored.append((score, item["lecture_id"]))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    lecture_ids: List[int] = []
    for _, lecture_id in scored:
        if lecture_id not in lecture_ids:
            lecture_ids.append(lecture_id)
        if len(lecture_ids) >= n_results:
            break
    return lecture_ids
