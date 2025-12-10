# app/db/models/transcript_utterance.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, func, UniqueConstraint
from app.db.base import Base
from datetime import datetime

from app.db.data_models.transcript import Transcript

class TranscriptUtterance(Base):
    __tablename__ = "transcript_utterances"
    __table_args__ = (
        UniqueConstraint("transcript_id", "start", name="uq_utterance_transcript_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transcript_id: Mapped[str] = mapped_column(ForeignKey("transcripts.id", ondelete="CASCADE"))
    start: Mapped[int]
    end: Mapped[int]
    confidence: Mapped[float]
    speaker: Mapped[str]
    text: Mapped[str]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    transcript: Mapped["Transcript"] = relationship(back_populates="utterances")
