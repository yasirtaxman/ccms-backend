"""Add medical management profiles, visits, medications, vaccinations, and documents.

Revision ID: d4e82a7c190b
Revises: a3c91e5d7b20
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e82a7c190b"
down_revision: Union[str, Sequence[str], None] = "a3c91e5d7b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def actor_columns() -> list[sa.Column]:
    return [
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    ]


def actor_foreign_keys() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
    ]


def upgrade() -> None:
    op.create_table(
        "medical_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("blood_group", sa.String(5), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("chronic_diseases", sa.Text(), nullable=True),
        sa.Column("disabilities", sa.Text(), nullable=True),
        sa.Column("special_needs", sa.Text(), nullable=True),
        sa.Column("height_cm", sa.Numeric(6, 2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(6, 2), nullable=True),
        sa.Column("emergency_notes", sa.Text(), nullable=True),
        *actor_columns(),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("child_id", name="uq_medical_profiles_child_id"),
        *actor_foreign_keys(),
    )
    op.create_index("ix_medical_profiles_child_id", "medical_profiles", ["child_id"])

    op.create_table(
        "medical_visits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("doctor_name", sa.String(255), nullable=False),
        sa.Column("hospital_name", sa.String(255), nullable=True),
        sa.Column("visit_type", sa.String(20), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=True),
        sa.Column("diagnosis", sa.Text(), nullable=True),
        sa.Column("treatment", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *actor_columns(),
        sa.CheckConstraint("visit_type IN ('Routine', 'Emergency', 'Specialist', 'Follow-up')", name="ck_medical_visits_type"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        *actor_foreign_keys(),
    )
    op.create_index("ix_medical_visits_child_id", "medical_visits", ["child_id"])
    op.create_index("ix_medical_visits_visit_date", "medical_visits", ["visit_date"])
    op.create_index("ix_medical_visits_child_date", "medical_visits", ["child_id", "visit_date"])

    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("medicine_name", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("prescribing_doctor", sa.String(255), nullable=True),
        sa.Column("status", sa.String(15), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *actor_columns(),
        sa.CheckConstraint("status IN ('Active', 'Completed', 'Stopped')", name="ck_medications_status"),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_medications_date_range"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        *actor_foreign_keys(),
    )
    op.create_index("ix_medications_child_id", "medications", ["child_id"])
    op.create_index("ix_medications_status", "medications", ["status"])
    op.create_index("ix_medications_child_status", "medications", ["child_id", "status"])

    op.create_table(
        "vaccinations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("vaccine_name", sa.String(255), nullable=False),
        sa.Column("dose_number", sa.Integer(), nullable=False),
        sa.Column("vaccination_date", sa.Date(), nullable=False),
        sa.Column("next_due_date", sa.Date(), nullable=True),
        sa.Column("administered_by", sa.String(255), nullable=True),
        sa.Column("hospital_name", sa.String(255), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        *actor_columns(),
        sa.CheckConstraint("dose_number > 0", name="ck_vaccinations_dose_positive"),
        sa.CheckConstraint("next_due_date IS NULL OR next_due_date >= vaccination_date", name="ck_vaccinations_due_date"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        *actor_foreign_keys(),
    )
    op.create_index("ix_vaccinations_child_id", "vaccinations", ["child_id"])
    op.create_index("ix_vaccinations_next_due_date", "vaccinations", ["next_due_date"])
    op.create_index("ix_vaccinations_child_due", "vaccinations", ["child_id", "next_due_date"])

    op.create_table(
        "medical_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("medical_visit_id", sa.Integer(), nullable=True),
        sa.Column("document_type", sa.String(30), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "document_type IN ('Prescription', 'Lab Report', 'X-Ray', 'MRI', 'Ultrasound', 'Medical Certificate', 'Vaccination Card')",
            name="ck_medical_documents_type",
        ),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["medical_visit_id"], ["medical_visits.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("stored_filename", name="uq_medical_documents_stored_filename"),
    )
    op.create_index("ix_medical_documents_child_id", "medical_documents", ["child_id"])
    op.create_index("ix_medical_documents_medical_visit_id", "medical_documents", ["medical_visit_id"])
    op.create_index("ix_medical_documents_child_visit", "medical_documents", ["child_id", "medical_visit_id"])


def downgrade() -> None:
    op.drop_table("medical_documents")
    op.drop_table("vaccinations")
    op.drop_table("medications")
    op.drop_table("medical_visits")
    op.drop_table("medical_profiles")
