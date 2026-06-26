import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import time
from app.database import SessionLocal
from app import models

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def encode_multipart_formdata(fields, files):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    lines = []

    for name, value in fields:
        lines.append(f"--{boundary}")
        lines.append(f"Content-Disposition: form-data; name=\"{name}\"")
        lines.append("")
        lines.append(value)

    for name, filename, value in files:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        lines.append(f"--{boundary}")
        lines.append(f"Content-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"")
        lines.append(f"Content-Type: {content_type}")
        lines.append("")
        lines.append(value)

    lines.append(f"--{boundary}--")
    body = b""
    for item in lines:
        if isinstance(item, str):
            body += item.encode("utf-8")
        else:
            body += item
        body += b"\r\n"

    return f"multipart/form-data; boundary={boundary}", body


def request(method, path, data=None, headers=None):
    url = BASE_URL + path
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        try:
            payload = err.read().decode("utf-8")
            return err.code, json.loads(payload)
        except Exception:
            return err.code, payload
    except Exception as err:
        return None, str(err)


def health_check():
    return request("GET", "/api/health")


def register_user(email, password="TestPassword123", name="Test User"):
    return request("POST", "/api/auth/register", {"name": name, "email": email, "password": password})


def login_user(email, password="TestPassword123"):
    data = urllib.parse.urlencode({"username": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(BASE_URL + "/api/auth/token", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        try:
            payload = err.read().decode("utf-8")
            return err.code, json.loads(payload)
        except Exception:
            return err.code, payload
    except Exception as err:
        return None, str(err)


def get_current_user(token):
    return request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token}"})


def get_history(token):
    return request("GET", "/api/history", headers={"Authorization": f"Bearer {token}"})


def create_local_test_lecture(email: str):
    with SessionLocal() as db:
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            return None
        lecture = models.Lecture(
            user_id=user.id,
            file_name="dummy.mp3",
            file_path=os.path.join("uploads", "dummy.mp3"),
            status="uploaded",
        )
        db.add(lecture)
        db.commit()
        db.refresh(lecture)
        transcript = models.Transcript(
            lecture_id=lecture.id,
            transcript="This is a sample lecture transcript about AI and machine learning.",
        )
        db.add(transcript)
        db.commit()
        return lecture.id


def upload_audio_file(token, file_path: str):
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    content_type, body = encode_multipart_formdata([], [("file", os.path.basename(file_path), file_bytes)])
    req = urllib.request.Request(BASE_URL + "/api/upload", data=body, method="POST")
    req.add_header("Content-Type", content_type)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        try:
            payload = err.read().decode("utf-8")
            return err.code, json.loads(payload)
        except Exception:
            return err.code, payload
    except Exception as err:
        return None, str(err)


def transcribe_lecture(token, lecture_id: int):
    return request("POST", f"/api/transcribe/{lecture_id}", headers={"Authorization": f"Bearer {token}"})


def create_summary(token, lecture_id: int):
    return request("POST", f"/api/summary/{lecture_id}", headers={"Authorization": f"Bearer {token}"})


def create_quiz(token, lecture_id: int):
    return request("POST", f"/api/quiz/{lecture_id}", headers={"Authorization": f"Bearer {token}"})


def create_flashcards(token, lecture_id: int):
    return request("POST", f"/api/flashcards/{lecture_id}", headers={"Authorization": f"Bearer {token}"})


def get_lecture_detail(token, lecture_id: int):
    return request("GET", f"/api/lecture/{lecture_id}", headers={"Authorization": f"Bearer {token}"})


def inject_transcript_for_lecture(email: str, lecture_id: int, transcript_text: str):
    with SessionLocal() as db:
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            return False
        lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == user.id).first()
        if not lecture:
            return False
        existing_transcript = db.query(models.Transcript).filter(models.Transcript.lecture_id == lecture.id).first()
        if existing_transcript:
            existing_transcript.transcript = transcript_text
        else:
            transcript = models.Transcript(lecture_id=lecture.id, transcript=transcript_text)
            db.add(transcript)
        lecture.status = "transcribed"
        db.commit()
        return True


def search_lectures(token, query):
    return request("GET", f"/api/search?q={urllib.parse.quote(query)}", headers={"Authorization": f"Bearer {token}"})


def chat_about_lecture(token, question, lecture_id=None):
    payload = {"question": question}
    if lecture_id:
        payload["lecture_id"] = lecture_id
    return request("POST", "/api/chat", data=payload, headers={"Authorization": f"Bearer {token}"})


if __name__ == "__main__":
    print("Health check:")
    code, payload = health_check()
    print(code, payload)

    email = f"testuser+{int(time.time())}@example.com"
    print(f"Registering user {email}")
    code, payload = register_user(email)
    print(code, payload)

    if code != 200:
        print("Registration failed, trying login with same credentials")

    code, payload = login_user(email)
    print(code, payload)
    if code != 200:
        print("Login failed, exiting.")
        raise SystemExit(1)

    token = payload.get("access_token")
    print("Token acquired", bool(token))

    print("Current user:")
    print(get_current_user(token))

    dummy_path = os.path.join("uploads", "dummy.mp3")
    with open(dummy_path, "wb") as f:
        f.write(b"RIFF....WAVEfmt ")

    print("Uploading dummy audio file:")
    upload_code, upload_payload = upload_audio_file(token, dummy_path)
    print(upload_code, upload_payload)

    if upload_code != 200:
        raise SystemExit("Upload failed")

    lecture_id = upload_payload.get("lecture_id")
    print("Uploaded lecture id:", lecture_id)

    print("Transcribing lecture:")
    print(transcribe_lecture(token, lecture_id))

    print("Creating summary:")
    print(create_summary(token, lecture_id))

    print("Creating quiz:")
    print(create_quiz(token, lecture_id))

    print("Creating flashcards:")
    print(create_flashcards(token, lecture_id))

    print("Lecture detail:")
    print(get_lecture_detail(token, lecture_id))

    print("Lecture history:")
    print(get_history(token))

    print("Search lectures:")
    print(search_lectures(token, "AI"))

    print("Chat about lecture:")
    print(chat_about_lecture(token, "What was the lecture about?", lecture_id=lecture_id))
