from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class MedicalDocument(Base):
    __tablename__ = "medical_documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('Prescription', 'Lab Report', 'X-Ray', 'MRI', "
            "'Ultrasound', 'Medical Certificate', 'Vaccination Card')",
            name="ck_medical_documents_type",
        ),
        Index("ix_medical_documents_child_visit", "child_id", "medical_visit_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(
        ForeignKey("children.id", ondelete="RESTRICT"), index=True
    )
    medical_visit_id: Mapped[int | None] = mapped_column(
        ForeignKey("medical_visits.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    document_type: Mapped[str] = mapped_column(String(30))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    file_path: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
