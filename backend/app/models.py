from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


def now():
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    password = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=now)
    lectures = relationship("Lecture", back_populates="owner")


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    upload_date = Column(DateTime, default=now)
    status = Column(String(32), default="uploaded")
    topic = Column(String(128), nullable=True)
    owner = relationship("User", back_populates="lectures")
    transcript = relationship("Transcript", back_populates="lecture", uselist=False)
    notes = relationship("Note", back_populates="lecture", uselist=False)
    quizzes = relationship("Quiz", back_populates="lecture")
    flashcards = relationship("Flashcard", back_populates="lecture")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    transcript = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)
    lecture = relationship("Lecture", back_populates="transcript")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    summary = Column(Text, nullable=False)
    key_points = Column(Text, nullable=True)
    mind_map = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    lecture = relationship("Lecture", back_populates="notes")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    question = Column(Text, nullable=False)
    option_a = Column(String(512), nullable=False)
    option_b = Column(String(512), nullable=False)
    option_c = Column(String(512), nullable=False)
    option_d = Column(String(512), nullable=False)
    answer = Column(String(512), nullable=False)
    difficulty = Column(String(32), default="medium")
    lecture = relationship("Lecture", back_populates="quizzes")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    lecture = relationship("Lecture", back_populates="flashcards")
