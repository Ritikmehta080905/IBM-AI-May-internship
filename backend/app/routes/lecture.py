import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.config import UPLOAD_DIR, ALLOWED_AUDIO_EXTENSIONS, ALLOWED_DOC_EXTENSIONS, MAX_UPLOAD_SIZE
from app.routes.auth import get_current_user
from app.utils import openai_client, vector_store

router = APIRouter()


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_AUDIO_EXTENSIONS or ext in ALLOWED_DOC_EXTENSIONS


@router.post("/upload", response_model=schemas.UploadResponse)
def upload_audio(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Supported formats: mp3, wav, m4a, pdf, png, jpg, jpeg."
        )
    contents = file.file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 100 MB limit.")
    file_extension = os.path.splitext(file.filename)[1].lower()
    safe_file_name = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, safe_file_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    lecture = models.Lecture(user_id=current_user.id, file_name=file.filename, file_path=file_path, status="uploaded")
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    return {"lecture_id": lecture.id}


@router.post("/transcribe/{lecture_id}", response_model=schemas.TranscriptionResponse)
def transcribe_lecture(lecture_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")
    try:
        file_extension = os.path.splitext(lecture.file_path)[1].lower().replace(".", "")
        if file_extension in ALLOWED_DOC_EXTENSIONS:
            transcript_text = openai_client.extract_text_from_doc(lecture.file_path)
        else:
            transcript_text = openai_client.transcribe_audio(lecture.file_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    transcript = models.Transcript(lecture_id=lecture.id, transcript=transcript_text)
    lecture.status = "transcribed"
    db.add(transcript)
    db.commit()
    vector_store.index_transcript(lecture.id, current_user.id, transcript_text)
    db.refresh(transcript)
    return {"lecture_id": lecture.id, "transcript": transcript_text}


@router.post("/summary/{lecture_id}", response_model=schemas.SummaryResponse)
def create_summary(lecture_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture or not lecture.transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found for lecture")
    try:
        result = openai_client.generate_summary(lecture.transcript.transcript)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    note = db.query(models.Note).filter(models.Note.lecture_id == lecture.id).first()
    if note:
        note.summary = result["summary"]
        note.key_points = result.get("key_points", "")
        note.mind_map = result.get("mind_map", "")
    else:
        note = models.Note(
            lecture_id=lecture.id,
            summary=result["summary"],
            key_points=result.get("key_points", ""),
            mind_map=result.get("mind_map", ""),
        )
        db.add(note)
    lecture.topic = result.get("main_topic", "General Lecture")
    lecture.status = "summarized"
    db.commit()
    db.refresh(note)
    return {"lecture_id": lecture.id, "summary": note.summary, "key_points": note.key_points}


@router.post("/quiz/{lecture_id}", response_model=schemas.QuizStatusResponse)
def create_quiz(lecture_id: int, difficulty: str = "medium", current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture or not lecture.transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found for lecture")
    try:
        quiz_items = openai_client.generate_quiz(lecture.transcript.transcript, difficulty=difficulty)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if not quiz_items:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Quiz generation failed.")
    db.query(models.Quiz).filter(models.Quiz.lecture_id == lecture.id).delete(synchronize_session="fetch")
    for item in quiz_items:
        quiz = models.Quiz(
            lecture_id=lecture.id,
            question=item.get("question", ""),
            option_a=item.get("option_a", ""),
            option_b=item.get("option_b", ""),
            option_c=item.get("option_c", ""),
            option_d=item.get("option_d", ""),
            answer=item.get("answer", ""),
            difficulty=difficulty,
        )
        db.add(quiz)
    lecture.status = "quiz_generated"
    db.commit()
    return {"lecture_id": lecture.id, "quiz_count": len(quiz_items)}


@router.post("/flashcards/{lecture_id}", response_model=schemas.FlashcardStatusResponse)
def create_flashcards(lecture_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture or not lecture.transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found for lecture")
    try:
        flashcards = openai_client.generate_flashcards(lecture.transcript.transcript)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if not flashcards:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Flashcard generation failed.")
    db.query(models.Flashcard).filter(models.Flashcard.lecture_id == lecture.id).delete(synchronize_session="fetch")
    for item in flashcards:
        card = models.Flashcard(
            lecture_id=lecture.id,
            question=item.get("question", ""),
            answer=item.get("answer", ""),
        )
        db.add(card)
    lecture.status = "flashcards_generated"
    db.commit()
    return {"lecture_id": lecture.id, "flashcard_count": len(flashcards)}


@router.get("/history", response_model=List[schemas.LectureResponse])
def lecture_history(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lectures = db.query(models.Lecture).filter(models.Lecture.user_id == current_user.id).all()
    return lectures


@router.get("/lecture/{lecture_id}", response_model=schemas.LectureResponse)
def get_lecture_detail(lecture_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")
    return lecture


@router.get("/lecture/{lecture_id}/transcript", response_model=schemas.TranscriptResponse)
def get_lecture_transcript(lecture_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture or not lecture.transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found for lecture")
    return lecture.transcript


@router.get("/lecture/{lecture_id}/notes", response_model=schemas.NoteResponse)
def get_lecture_notes(lecture_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture or not lecture.notes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notes not found for lecture")
    return lecture.notes


@router.get("/lecture/{lecture_id}/quiz", response_model=List[schemas.QuizResponse])
def get_lecture_quiz(lecture_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")
    return lecture.quizzes


@router.get("/lecture/{lecture_id}/flashcards", response_model=List[schemas.FlashcardResponse])
def get_lecture_flashcards(lecture_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = db.query(models.Lecture).filter(models.Lecture.id == lecture_id, models.Lecture.user_id == current_user.id).first()
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")
    return lecture.flashcards


@router.get("/search", response_model=List[schemas.LectureResponse])
def search_lectures(q: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query string is required.")
    lectures = (
        db.query(models.Lecture)
        .join(models.Transcript)
        .filter(models.Lecture.user_id == current_user.id)
        .filter(models.Transcript.transcript.contains(q))
        .all()
    )
    return lectures


@router.get("/search/semantic", response_model=schemas.SearchResponse)
def semantic_search(q: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query string is required.")
    lecture_ids = vector_store.find_lecture_ids_for_query(q, current_user.id)
    lectures = db.query(models.Lecture).filter(models.Lecture.user_id == current_user.id, models.Lecture.id.in_(lecture_ids)).all()
    lecture_map = {lecture.id: lecture for lecture in lectures}
    results = [
        schemas.SearchResultItem(
            id=lecture_id,
            file_name=lecture_map[lecture_id].file_name,
            upload_date=lecture_map[lecture_id].upload_date,
            status=lecture_map[lecture_id].status,
        )
        for lecture_id in lecture_ids
        if lecture_id in lecture_map
    ]
    return {"query": q, "results": results}


@router.post("/chat", response_model=schemas.ChatResponse)
def chat_about_lecture(request: schemas.ChatRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    lecture = None
    if request.lecture_id:
        lecture = db.query(models.Lecture).filter(models.Lecture.id == request.lecture_id, models.Lecture.user_id == current_user.id).first()
        if not lecture:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")
    else:
        lecture = (
            db.query(models.Lecture)
            .filter(models.Lecture.user_id == current_user.id)
            .order_by(models.Lecture.upload_date.desc())
            .first()
        )
        if not lecture:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No lectures available")

    sources = None
    if request.use_rag:
        chunks = vector_store.search_relevant_chunks(request.question, current_user.id, request.lecture_id)
        if chunks:
            context = "\n\n".join(c["excerpt"] for c in chunks)
            sources = [f"Lecture {c['lecture_id']} chunk {c['chunk_index']}" for c in chunks]
            try:
                answer = openai_client.answer_question_with_context(request.question, context)
            except RuntimeError as exc:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
            return {"answer": answer, "sources": sources}

    if lecture.transcript and lecture.transcript.transcript:
        context = lecture.transcript.transcript
    elif lecture.notes and lecture.notes.summary:
        context = lecture.notes.summary
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture content is not available for chat")

    try:
        answer = openai_client.answer_question(request.question, context)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return {"answer": answer, "sources": sources}
