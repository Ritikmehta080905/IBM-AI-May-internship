import httpx
import sys
import time
import os
import wave
import struct

BASE_URL = "http://127.0.0.1:8000/api"
AUDIO_PATH = "operating_systems_lecture.wav"

def generate_dummy_wav():
    print(f"Generating dummy WAV file: {AUDIO_PATH}...")
    with wave.open(AUDIO_PATH, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        # Write 2 seconds of silent audio frames
        for _ in range(16000):
            w.writeframes(struct.pack('h', 0))
    print("WAV file generated successfully.")

def run_extended_tests():
    print("Starting Extended Backend Integration & Security Tests...")
    
    # Ensure dummy audio file is generated
    generate_dummy_wav()
    
    client = httpx.Client(timeout=30.0)
    
    # Generate unique emails
    email_a = f"user_a_{int(time.time())}@example.com"
    email_b = f"user_b_{int(time.time())}@example.com"
    password = "SecurePassword123!"
    
    # 1. TEST SECURITY & ACCESS CONTROL
    print("\n--- 1. Testing Security & Access Control ---")
    
    # 1a. Call without token
    print("Attempting to fetch history without auth token...")
    r = client.get(f"{BASE_URL}/history")
    print(f"Status (Expected 401): {r.status_code}")
    if r.status_code != 401:
        print(f"FAILED: Expected 401, got {r.status_code}")
        sys.exit(1)
        
    # 1b. Call with invalid token
    print("Attempting to fetch history with invalid token...")
    r = client.get(f"{BASE_URL}/history", headers={"Authorization": "Bearer invalidtoken123"})
    print(f"Status (Expected 401): {r.status_code}")
    if r.status_code != 401:
        print(f"FAILED: Expected 401, got {r.status_code}")
        sys.exit(1)
        
    # 2. TEST DUPLICATE REGISTRATION
    print("\n--- 2. Testing Duplicate User Registration ---")
    
    # 2a. Register User A
    print(f"Registering User A ({email_a})...")
    reg_data = {"name": "User A", "email": email_a, "password": password}
    r = client.post(f"{BASE_URL}/auth/register", json=reg_data)
    print(f"Status (Expected 200): {r.status_code}")
    if r.status_code != 200:
        print(f"FAILED: {r.text}")
        sys.exit(1)
        
    token_a = r.json().get("access_token")
    
    # 2b. Register same user again
    print("Registering User A again to trigger conflict...")
    r = client.post(f"{BASE_URL}/auth/register", json=reg_data)
    print(f"Status (Expected 400): {r.status_code}")
    if r.status_code != 400:
        print(f"FAILED: Expected 400, got {r.status_code}")
        sys.exit(1)
    print(f"Response: {r.json()}")
    if "already registered" not in r.json().get("detail", "").lower():
        print("FAILED: Expected 'Email already registered' message")
        sys.exit(1)

    # 3. TEST RESOURCE ISOLATION
    print("\n--- 3. Testing Resource Isolation ---")
    
    # 3a. User A uploads a valid WAV file
    print("User A uploading operating_systems_lecture.wav...")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    files = {"file": (AUDIO_PATH, open(AUDIO_PATH, "rb"), "audio/wav")}
    r = client.post(f"{BASE_URL}/upload", files=files, headers=headers_a)
    print(f"Status (Expected 200): {r.status_code}")
    if r.status_code != 200:
        print(f"FAILED: {r.text}")
        sys.exit(1)
        
    lecture_id_a = r.json().get("lecture_id")
    print(f"Uploaded. Lecture ID: {lecture_id_a}")
    
    # 3b. Register User B
    print(f"Registering User B ({email_b})...")
    reg_data_b = {"name": "User B", "email": email_b, "password": password}
    r = client.post(f"{BASE_URL}/auth/register", json=reg_data_b)
    token_b = r.json().get("access_token")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # 3c. User B attempts to access User A's lecture detail
    print(f"User B attempting to view User A's lecture {lecture_id_a}...")
    r = client.get(f"{BASE_URL}/lecture/{lecture_id_a}", headers=headers_b)
    print(f"Status (Expected 404): {r.status_code}")
    if r.status_code != 404:
        print(f"FAILED: Expected 404, got {r.status_code}")
        sys.exit(1)
        
    # 3d. User B attempts to run transcription on User A's lecture
    print(f"User B attempting to transcribe User A's lecture {lecture_id_a}...")
    r = client.post(f"{BASE_URL}/transcribe/{lecture_id_a}", headers=headers_b)
    print(f"Status (Expected 404): {r.status_code}")
    if r.status_code != 404:
        print(f"FAILED: Expected 404, got {r.status_code}")
        sys.exit(1)

    # 4. TEST INVALID FILE UPLOADS
    print("\n--- 4. Testing Unsupported File Type Upload ---")
    
    # Create a dummy text file
    with open("invalid_doc.txt", "w") as f:
        f.write("This file should not be allowed.")
        
    print("Attempting to upload invalid_doc.txt...")
    files_invalid = {"file": ("invalid_doc.txt", open("invalid_doc.txt", "rb"), "text/plain")}
    r = client.post(f"{BASE_URL}/upload", files=files_invalid, headers=headers_a)
    print(f"Status (Expected 400): {r.status_code}")
    if r.status_code != 400:
        print(f"FAILED: Expected 400, got {r.status_code}")
        sys.exit(1)
    print(f"Response: {r.json()}")
    if "invalid file type" not in r.json().get("detail", "").lower():
        print("FAILED: Expected 'Invalid file type' detail message")
        sys.exit(1)
        
    # Clean up temp invalid file
    try:
        os.remove("invalid_doc.txt")
    except OSError:
        pass

    # 5. TEST AUDIO TRANSCRIPTION
    print("\n--- 5. Testing WAV Audio Transcription ---")
    
    # User A transcribes their WAV file
    print(f"User A requesting transcription for lecture {lecture_id_a}...")
    r = client.post(f"{BASE_URL}/transcribe/{lecture_id_a}", headers=headers_a)
    print(f"Status (Expected 200): {r.status_code}")
    if r.status_code != 200:
        print(f"FAILED: {r.text}")
        sys.exit(1)
    transcript = r.json().get("transcript", "")
    print(f"Extracted Transcript (length={len(transcript)}): {transcript[:120]}...")
    if not transcript:
        print("FAILED: Transcript is empty")
        sys.exit(1)

    # 6. TEST DIFFERENT QUIZ DIFFICULTIES
    print("\n--- 6. Testing Quiz Generation Difficulties ---")
    
    # 6a. Easy Quiz
    print("Generating Easy Quiz...")
    r = client.post(f"{BASE_URL}/quiz/{lecture_id_a}?difficulty=easy", headers=headers_a)
    print(f"Status (Expected 200): {r.status_code}")
    if r.status_code != 200:
        print(f"FAILED: {r.text}")
        sys.exit(1)
    print(f"Easy Quiz status: {r.json()}")
    
    # Retrieve Easy Quiz Questions
    r = client.get(f"{BASE_URL}/lecture/{lecture_id_a}/quiz", headers=headers_a)
    questions_easy = r.json()
    print(f"Easy quiz contains {len(questions_easy)} questions.")
    if len(questions_easy) == 0:
        print("FAILED: No questions in easy quiz")
        sys.exit(1)
    print(f"Sample Question: {questions_easy[0].get('question')}")
    
    # 6b. Hard Quiz
    print("Generating Hard Quiz...")
    r = client.post(f"{BASE_URL}/quiz/{lecture_id_a}?difficulty=hard", headers=headers_a)
    print(f"Status (Expected 200): {r.status_code}")
    if r.status_code != 200:
        print(f"FAILED: {r.text}")
        sys.exit(1)
    print(f"Hard Quiz status: {r.json()}")
    
    # Retrieve Hard Quiz Questions
    r = client.get(f"{BASE_URL}/lecture/{lecture_id_a}/quiz", headers=headers_a)
    questions_hard = r.json()
    print(f"Hard quiz contains {len(questions_hard)} questions.")
    if len(questions_hard) == 0:
        print("FAILED: No questions in hard quiz")
        sys.exit(1)
    print(f"Sample Question: {questions_hard[0].get('question')}")

    # Clean up generated audio file
    try:
        os.remove(AUDIO_PATH)
    except OSError:
        pass

    print("\n=== All Extended Integration & Security Tests Passed Successfully! ===")

if __name__ == "__main__":
    run_extended_tests()
