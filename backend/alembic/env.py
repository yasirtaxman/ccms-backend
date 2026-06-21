from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

from app.core.database import Base
from app.core.config import settings

from app.models.child import Child
from app.models.document import Document
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.audit_log import AuditLog
from app.models.sponsor import Sponsor, ChildSponsorship
from app.models.accommodation import Building, Block, Floor, Room, Bed, BedAllocation
from app.models.medical_profile import MedicalProfile
from app.models.medical_visit import MedicalVisit
from app.models.medication import Medication
from app.models.vaccination import Vaccination
from app.models.medical_document import MedicalDocument
from app.models.school import School
from app.models.education_record import EducationRecord
from app.models.exam_result import ExamResult
from app.models.attendance import Attendance
from app.models.education_document import EducationDocument
from app.models.case_management import (
    ChildCaseProfile, CaseNote, CounselingSession, IncidentRecord, CarePlan, CaseReview
)
from app.models.child_attendance import DailyChildAttendance

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
