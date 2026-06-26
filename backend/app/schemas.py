from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseSchema):
    id: int
    name: str
    email: EmailStr


class Token(BaseSchema):
    access_token: str
    token_type: str


class TokenData(BaseSchema):
    email: Optional[str] = None


class UploadResponse(BaseSchema):
    lecture_id: int


class TranscriptionResponse(BaseSchema):
    lecture_id: int
    transcript: str


class SummaryResponse(BaseSchema):
    lecture_id: int
    summary: str
    key_points: Optional[str] = None


class QuizStatusResponse(BaseSchema):
    lecture_id: int
    quiz_count: int


class FlashcardStatusResponse(BaseSchema):
    lecture_id: int
    flashcard_count: int


class TranscriptResponse(BaseSchema):
    lecture_id: int
    transcript: str
    created_at: datetime


class NoteResponse(BaseSchema):
    lecture_id: int
    summary: str
    key_points: Optional[str]
    mind_map: Optional[str] = None
    created_at: datetime


class QuizResponse(BaseSchema):
    id: int
    lecture_id: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    answer: str
    difficulty: str


class FlashcardResponse(BaseSchema):
    id: int
    lecture_id: int
    question: str
    answer: str


class LectureResponse(BaseSchema):
    id: int
    file_name: str
    file_path: str
    upload_date: datetime
    status: str
    topic: Optional[str] = None
    transcript: Optional[TranscriptResponse] = None
    notes: Optional[NoteResponse] = None
    quizzes: Optional[List[QuizResponse]] = None
    flashcards: Optional[List[FlashcardResponse]] = None


class SearchResultItem(BaseSchema):
    id: int
    file_name: str
    upload_date: datetime
    status: str
    topic: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]


class ChatRequest(BaseModel):
    question: str
    lecture_id: Optional[int] = None
    use_rag: Optional[bool] = False


class ChatResponse(BaseSchema):
    answer: str
    sources: Optional[List[str]] = None
