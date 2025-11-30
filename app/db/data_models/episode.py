# app/db/models/episode.py
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base
from datetime import datetime

class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    podcast_id: Mapped[str] = mapped_column(ForeignKey("podcasts.id"))
    title: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True, default='')
    podcast_url: Mapped[str]
    podcast_image: Mapped[str]
    episode_image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    enclosure_url: Mapped[str]
    duration: Mapped[int]
    date_published: Mapped[datetime]
    host_questions: Mapped[list] = mapped_column(JSONB, default=list, nullable=True)
    question_answers: Mapped[list] = mapped_column(JSONB, default=list, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    podcast: Mapped["Podcast"] = relationship("Podcast", back_populates="episodes")
    transcript: Mapped["Transcript"] = relationship(
        back_populates="episode", uselist=False, 
        cascade="all, delete-orphan"
    )
