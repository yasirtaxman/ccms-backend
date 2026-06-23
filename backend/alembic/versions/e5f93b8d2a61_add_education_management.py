"""Add education management schools, history, results, attendance, and documents.

Revision ID: e5f93b8d2a61
Revises: d4e82a7c190b
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f93b8d2a61"
down_revision: Union[str, Sequence[str], None] = "d4e82a7c190b"
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
        "schools",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("school_code", sa.String(50), nullable=False),
        sa.Column("school_name", sa.String(255), nullable=False),
        sa.Column("school_type", sa.String(20), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("province", sa.String(100), nullable=True),
        sa.Column("contact_person", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(10), nullable=False),
        *actor_columns(),
        sa.CheckConstraint("school_type IN ('Government', 'Private', 'Madrassa', 'Technical', 'College', 'University')", name="ck_schools_type"),
        sa.CheckConstraint("status IN ('Active', 'Inactive')", name="ck_schools_status"),
        sa.UniqueConstraint("school_code", name="uq_schools_school_code"),
        *actor_foreign_keys(),
    )
    op.create_index("ix_schools_school_code", "schools", ["school_code"])
    op.create_index("ix_schools_status_type", "schools", ["status", "school_type"])

    op.create_table(
        "education_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("admission_number", sa.String(100), nullable=True),
        sa.Column("class_level", sa.String(50), nullable=False),
        sa.Column("academic_year", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(15), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        *actor_columns(),
        sa.CheckConstraint("status IN ('Studying', 'Completed', 'Dropped', 'Transferred')", name="ck_education_records_status"),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_education_records_dates"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="RESTRICT"),
        *actor_foreign_keys(),
    )
    op.create_index("ix_education_records_child_id", "education_records", ["child_id"])
    op.create_index("ix_education_records_school_id", "education_records", ["school_id"])
    op.create_index("ix_education_records_child_status", "education_records", ["child_id", "status"])
    op.create_index("ix_education_records_school_year", "education_records", ["school_id", "academic_year"])
    op.create_index("uq_education_records_active_child", "education_records", ["child_id"], unique=True, postgresql_where=sa.text("status = 'Studying'"))

    op.create_table(
        "exam_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("education_record_id", sa.Integer(), nullable=False),
        sa.Column("exam_name", sa.String(20), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("total_marks", sa.Numeric(8, 2), nullable=False),
        sa.Column("obtained_marks", sa.Numeric(8, 2), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("grade", sa.String(10), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        *actor_columns(),
        sa.CheckConstraint("exam_name IN ('Monthly', 'Quarterly', 'Midterm', 'Annual', 'Board')", name="ck_exam_results_name"),
        sa.CheckConstraint("total_marks > 0", name="ck_exam_results_total_marks"),
        sa.CheckConstraint("obtained_marks >= 0 AND obtained_marks <= total_marks", name="ck_exam_results_marks"),
        sa.CheckConstraint("percentage >= 0 AND percentage <= 100", name="ck_exam_results_percentage"),
        sa.ForeignKeyConstraint(["education_record_id"], ["education_records.id"], ondelete="RESTRICT"),
        *actor_foreign_keys(),
    )
    op.create_index("ix_exam_results_education_record_id", "exam_results", ["education_record_id"])
    op.create_index("ix_exam_results_exam_name", "exam_results", ["exam_name"])
    op.create_index("ix_exam_results_exam_date", "exam_results", ["exam_date"])
    op.create_index("ix_exam_results_record_date", "exam_results", ["education_record_id", "exam_date"])

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("education_record_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.Column("present_days", sa.Integer(), nullable=False),
        sa.Column("absent_days", sa.Integer(), nullable=False),
        sa.Column("attendance_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        *actor_columns(),
        sa.CheckConstraint("month >= 1 AND month <= 12", name="ck_attendance_month"),
        sa.CheckConstraint("year >= 1900 AND year <= 2200", name="ck_attendance_year"),
        sa.CheckConstraint("total_days > 0", name="ck_attendance_total_days"),
        sa.CheckConstraint("present_days >= 0 AND absent_days >= 0", name="ck_attendance_nonnegative"),
        sa.CheckConstraint("present_days + absent_days = total_days", name="ck_attendance_day_totals"),
        sa.CheckConstraint("attendance_percentage >= 0 AND attendance_percentage <= 100", name="ck_attendance_percentage"),
        sa.ForeignKeyConstraint(["education_record_id"], ["education_records.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("education_record_id", "month", "year", name="uq_attendance_record_month_year"),
        *actor_foreign_keys(),
    )
    op.create_index("ix_attendance_education_record_id", "attendance", ["education_record_id"])
    op.create_index("ix_attendance_record_period", "attendance", ["education_record_id", "year", "month"])

    op.create_table(
        "education_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("education_record_id", sa.Integer(), nullable=True),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("document_type IN ('School Admission', 'School Leaving Certificate', 'Result Card', 'Board Certificate', 'Degree', 'Transcript', 'Character Certificate')", name="ck_education_documents_type"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["education_record_id"], ["education_records.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("stored_filename", name="uq_education_documents_stored_filename"),
    )
    op.create_index("ix_education_documents_child_id", "education_documents", ["child_id"])
    op.create_index("ix_education_documents_education_record_id", "education_documents", ["education_record_id"])
    op.create_index("ix_education_documents_child_record", "education_documents", ["child_id", "education_record_id"])


def downgrade() -> None:
    op.drop_table("education_documents")
    op.drop_table("attendance")
    op.drop_table("exam_results")
    op.drop_table("education_records")
    op.drop_table("schools")
