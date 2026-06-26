import httpx
import sys
import time

BASE_URL = "http://127.0.0.1:8000/api"
PDF_PATH = "../computer_networks_lecture.pdf"

def run_test():
    print("Starting End-to-End API Test...")
    
    # Generate unique user credentials
    username = f"e2e_user_{int(time.time())}@example.com"
    password = "E2ePassword123!"
    
    client = httpx.Client(timeout=30.0)
    
    # 1. Register User
    print("\n--- 1. Registering User ---")
    reg_data = {
        "name": "E2E Test User",
        "email": username,
        "password": password
    }
    r = client.post(f"{BASE_URL}/auth/register", json=reg_data)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Failed: {r.text}")
        sys.exit(1)
    
    token = r.json().get("access_token")
    print(f"Token acquired: {token[:15]}...")
    
    # Add auth token header
    client.headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Upload PDF
    print("\n--- 2. Uploading PDF Lecture ---")
    files = {"file": ("computer_networks_lecture.pdf", open(PDF_PATH, "rb"), "application/pdf")}
    r = client.post(f"{BASE_URL}/upload", files=files)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Failed: {r.text}")
        sys.exit(1)
        
    lecture_id = r.json().get("lecture_id")
    print(f"Uploaded successfully. Lecture ID: {lecture_id}")
    
    # 3. Transcribe / OCR
    print("\n--- 3. Extracting Text (OCR) ---")
    r = client.post(f"{BASE_URL}/transcribe/{lecture_id}")
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Failed: {r.text}")
        sys.exit(1)
    print(f"Transcript: {r.json().get('transcript')[:100]}...")
    
    # 4. Generate Notes
    print("\n--- 4. Generating Notes ---")
    r = client.post(f"{BASE_URL}/summary/{lecture_id}")
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Failed: {r.text}")
        sys.exit(1)
    print(f"Notes Topic: {r.json().get('topic') or 'Not returned'}")
    print(f"Summary: {r.json().get('summary')[:100]}...")
    
    # 5. Generate Quiz
    print("\n--- 5. Generating Quiz ---")
    r = client.post(f"{BASE_URL}/quiz/{lecture_id}?difficulty=medium")
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Failed: {r.text}")
        sys.exit(1)
    print(f"Quiz status: {r.json()}")
    
    # 6. Generate Flashcards
    print("\n--- 6. Generating Flashcards ---")
    r = client.post(f"{BASE_URL}/flashcards/{lecture_id}")
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Failed: {r.text}")
        sys.exit(1)
    print(f"Flashcards status: {r.json()}")
    
    # 7. Get Lecture details
    print("\n--- 7. Retrieving Lecture Details ---")
    r = client.get(f"{BASE_URL}/lecture/{lecture_id}")
    print(f"Status: {r.status_code}")
    details = r.json()
    print(f"Lecture Status: {details.get('status')}")
    print(f"Quizzes count: {len(details.get('quizzes', []))}")
    print(f"Flashcards count: {len(details.get('flashcards', []))}")
    
    # 8. Semantic Search
    print("\n--- 8. Semantic Search ---")
    r = client.get(f"{BASE_URL}/search/semantic?q=network")
    print(f"Status: {r.status_code}")
    print(f"Semantic Search Results: {r.json()}")
    
    # 9. RAG Chat
    print("\n--- 9. RAG Chat ---")
    chat_payload = {
        "question": "What is a computer network layer?",
        "use_rag": True,
        "lecture_id": lecture_id
    }
    r = client.post(f"{BASE_URL}/chat", json=chat_payload)
    print(f"Status: {r.status_code}")
    print(f"Chat Answer: {r.json().get('answer')}")
    print(f"Chat Sources: {r.json().get('sources')}")

    print("\n=== End-to-End API Test Successful ===")

if __name__ == "__main__":
    run_test()
