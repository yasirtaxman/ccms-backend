from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class SchoolType(str, Enum):
    GOVERNMENT = "Government"
    PRIVATE = "Private"
    MADRASSA = "Madrassa"
    TECHNICAL = "Technical"
    COLLEGE = "College"
    UNIVERSITY = "University"


class SchoolStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class EducationStatus(str, Enum):
    STUDYING = "Studying"
    COMPLETED = "Completed"
    DROPPED = "Dropped"
    TRANSFERRED = "Transferred"


class ExamName(str, Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    MIDTERM = "Midterm"
    ANNUAL = "Annual"
    BOARD = "Board"


class EducationDocumentType(str, Enum):
    SCHOOL_ADMISSION = "School Admission"
    SCHOOL_LEAVING = "School Leaving Certificate"
    RESULT_CARD = "Result Card"
    BOARD_CERTIFICATE = "Board Certificate"
    DEGREE = "Degree"
    TRANSCRIPT = "Transcript"
    CHARACTER_CERTIFICATE = "Character Certificate"


class SchoolCreate(BaseModel):
    school_code: str = Field(min_length=1, max_length=50, examples=["SCH-001"])
    school_name: str = Field(min_length=2, max_length=255)
    school_type: SchoolType
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    province: str | None = Field(default=None, max_length=100)
    contact_person: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9][0-9 ()-]{6,28}$")
    email: EmailStr | None = None
    status: SchoolStatus = SchoolStatus.ACTIVE
    model_config = ConfigDict(extra="forbid")


class SchoolUpdate(BaseModel):
    school_code: str | None = Field(default=None, min_length=1, max_length=50)
    school_name: str | None = Field(default=None, min_length=2, max_length=255)
    school_type: SchoolType | None = None
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    province: str | None = Field(default=None, max_length=100)
    contact_person: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9][0-9 ()-]{6,28}$")
    email: EmailStr | None = None
    status: SchoolStatus | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"school_code", "school_name", "school_type", "status"} & self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class SchoolResponse(SchoolCreate):
    id: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EducationRecordCreate(BaseModel):
    school_id: int = Field(gt=0)
    admission_number: str | None = Field(default=None, max_length=100)
    class_level: str = Field(min_length=1, max_length=50)
    academic_year: str = Field(min_length=4, max_length=20)
    start_date: date
    end_date: date | None = None
    status: EducationStatus = EducationStatus.STUDYING
    remarks: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class EducationRecordUpdate(BaseModel):
    admission_number: str | None = Field(default=None, max_length=100)
    class_level: str | None = Field(default=None, min_length=1, max_length=50)
    academic_year: str | None = Field(default=None, min_length=4, max_length=20)
    start_date: date | None = None
    end_date: date | None = None
    status: EducationStatus | None = None
    remarks: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"class_level", "academic_year", "start_date", "status"} & self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class EducationRecordResponse(EducationRecordCreate):
    id: int
    child_id: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ExamResultCreate(BaseModel):
    exam_name: ExamName
    exam_date: date
    total_marks: Decimal = Field(gt=0, decimal_places=2)
    obtained_marks: Decimal = Field(ge=0, decimal_places=2)
    grade: str | None = Field(default=None, max_length=10)
    position: int | None = Field(default=None, gt=0)
    remarks: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_marks(self):
        if self.obtained_marks > self.total_marks:
            raise ValueError("obtained_marks cannot exceed total_marks")
        return self


class ExamResultUpdate(BaseModel):
    exam_name: ExamName | None = None
    exam_date: date | None = None
    total_marks: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    obtained_marks: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    grade: str | None = Field(default=None, max_length=10)
    position: int | None = Field(default=None, gt=0)
    remarks: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"exam_name", "exam_date", "total_marks", "obtained_marks"} & self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class ExamResultResponse(ExamResultCreate):
    id: int
    education_record_id: int
    percentage: Decimal
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AttendanceCreate(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=1900, le=2200)
    total_days: int = Field(gt=0)
    present_days: int = Field(ge=0)
    absent_days: int = Field(ge=0)
    remarks: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_days(self):
        if self.present_days + self.absent_days != self.total_days:
            raise ValueError("present_days plus absent_days must equal total_days")
        return self


class AttendanceUpdate(BaseModel):
    month: int | None = Field(default=None, ge=1, le=12)
    year: int | None = Field(default=None, ge=1900, le=2200)
    total_days: int | None = Field(default=None, gt=0)
    present_days: int | None = Field(default=None, ge=0)
    absent_days: int | None = Field(default=None, ge=0)
    remarks: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"month", "year", "total_days", "present_days", "absent_days"} & self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class AttendanceResponse(AttendanceCreate):
    id: int
    education_record_id: int
    attendance_percentage: Decimal
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EducationDocumentResponse(BaseModel):
    id: int
    child_id: int
    education_record_id: int | None
    document_type: EducationDocumentType
    original_filename: str
    stored_filename: str
    file_path: str
    uploaded_by: int
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EducationDashboard(BaseModel):
    total_students: int
    active_students: int
    schools_count: int
    average_attendance: float
    average_marks: float
    board_students: int
    dropout_students: int
