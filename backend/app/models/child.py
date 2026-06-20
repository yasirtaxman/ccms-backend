from datetime import datetime, date

from sqlalchemy import String, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Child(Base):
    __tablename__ = "children"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identification
    child_id: Mapped[str] = mapped_column(String(50), unique=True)
    admission_file_no: Mapped[str] = mapped_column(String(50), unique=True)

    # Child Information
    full_name: Mapped[str] = mapped_column(String(255))
    father_name: Mapped[str] = mapped_column(String(255))
    grandfather_name: Mapped[str] = mapped_column(String(255))
    mother_name: Mapped[str] = mapped_column(String(255))

    gender: Mapped[str] = mapped_column(String(20))
    date_of_birth: Mapped[date] = mapped_column(Date)

    # Guardian Information
    guardian_name: Mapped[str] = mapped_column(String(255))
    guardian_relationship: Mapped[str] = mapped_column(String(100))
    guardian_cnic: Mapped[str] = mapped_column(String(20))
    guardian_mobile: Mapped[str] = mapped_column(String(20))

    # Address Information
    current_address: Mapped[str] = mapped_column(Text)
    permanent_address: Mapped[str] = mapped_column(Text)

    village_mohallah: Mapped[str] = mapped_column(String(255))
    union_council: Mapped[str] = mapped_column(String(255))
    tehsil: Mapped[str] = mapped_column(String(255))
    district: Mapped[str] = mapped_column(String(255))
    province: Mapped[str] = mapped_column(String(255))

    # Admission
    admission_date: Mapped[date] = mapped_column(Date)

    reason_for_admission: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )