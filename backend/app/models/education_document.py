from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class EducationDocument(Base):
    __tablename__ = "education_documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('School Admission', 'School Leaving Certificate', 'Result Card', "
            "'Board Certificate', 'Degree', 'Transcript', 'Character Certificate')",
            name="ck_education_documents_type",
        ),
        Index("ix_education_documents_child_record", "child_id", "education_record_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    education_record_id: Mapped[int | None] = mapped_column(ForeignKey("education_records.id", ondelete="RESTRICT"), nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(String(40))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    file_path: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
