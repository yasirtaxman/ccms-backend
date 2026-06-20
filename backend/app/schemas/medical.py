from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BloodGroup(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class VisitType(str, Enum):
    ROUTINE = "Routine"
    EMERGENCY = "Emergency"
    SPECIALIST = "Specialist"
    FOLLOW_UP = "Follow-up"


class MedicationStatus(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    STOPPED = "Stopped"


class MedicalDocumentType(str, Enum):
    PRESCRIPTION = "Prescription"
    LAB_REPORT = "Lab Report"
    X_RAY = "X-Ray"
    MRI = "MRI"
    ULTRASOUND = "Ultrasound"
    MEDICAL_CERTIFICATE = "Medical Certificate"
    VACCINATION_CARD = "Vaccination Card"


class MedicalProfileCreate(BaseModel):
    blood_group: BloodGroup | None = None
    allergies: str | None = None
    chronic_diseases: str | None = None
    disabilities: str | None = None
    special_needs: str | None = None
    height_cm: Decimal | None = Field(default=None, gt=0, le=300, decimal_places=2)
    weight_kg: Decimal | None = Field(default=None, gt=0, le=500, decimal_places=2)
    emergency_notes: str | None = None
    model_config = ConfigDict(extra="forbid")


class MedicalProfileUpdate(MedicalProfileCreate):
    pass


class MedicalProfileResponse(MedicalProfileCreate):
    id: int
    child_id: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MedicalVisitCreate(BaseModel):
    visit_date: date
    doctor_name: str = Field(min_length=2, max_length=255)
    hospital_name: str | None = Field(default=None, max_length=255)
    visit_type: VisitType
    symptoms: str | None = None
    diagnosis: str | None = None
    treatment: str | None = None
    notes: str | None = None
    model_config = ConfigDict(extra="forbid")


class MedicalVisitUpdate(BaseModel):
    visit_date: date | None = None
    doctor_name: str | None = Field(default=None, min_length=2, max_length=255)
    hospital_name: str | None = Field(default=None, max_length=255)
    visit_type: VisitType | None = None
    symptoms: str | None = None
    diagnosis: str | None = None
    treatment: str | None = None
    notes: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for field_name in {"visit_date", "doctor_name", "visit_type"} & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class MedicalVisitResponse(MedicalVisitCreate):
    id: int
    child_id: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MedicationCreate(BaseModel):
    medicine_name: str = Field(min_length=1, max_length=255)
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date | None = None
    prescribing_doctor: str | None = Field(default=None, max_length=255)
    status: MedicationStatus = MedicationStatus.ACTIVE
    notes: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class MedicationUpdate(BaseModel):
    medicine_name: str | None = Field(default=None, min_length=1, max_length=255)
    dosage: str | None = Field(default=None, min_length=1, max_length=100)
    frequency: str | None = Field(default=None, min_length=1, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    prescribing_doctor: str | None = Field(default=None, max_length=255)
    status: MedicationStatus | None = None
    notes: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        required = {"medicine_name", "dosage", "frequency", "start_date", "status"}
        for field_name in required & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class MedicationResponse(MedicationCreate):
    id: int
    child_id: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VaccinationCreate(BaseModel):
    vaccine_name: str = Field(min_length=1, max_length=255)
    dose_number: int = Field(gt=0)
    vaccination_date: date
    next_due_date: date | None = None
    administered_by: str | None = Field(default=None, max_length=255)
    hospital_name: str | None = Field(default=None, max_length=255)
    remarks: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.next_due_date is not None and self.next_due_date < self.vaccination_date:
            raise ValueError("next_due_date must be on or after vaccination_date")
        return self


class VaccinationUpdate(BaseModel):
    vaccine_name: str | None = Field(default=None, min_length=1, max_length=255)
    dose_number: int | None = Field(default=None, gt=0)
    vaccination_date: date | None = None
    next_due_date: date | None = None
    administered_by: str | None = Field(default=None, max_length=255)
    hospital_name: str | None = Field(default=None, max_length=255)
    remarks: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        required = {"vaccine_name", "dose_number", "vaccination_date"}
        for field_name in required & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class VaccinationResponse(VaccinationCreate):
    id: int
    child_id: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MedicalDocumentResponse(BaseModel):
    id: int
    child_id: int
    medical_visit_id: int | None
    document_type: MedicalDocumentType
    original_filename: str
    stored_filename: str
    file_path: str
    uploaded_by: int
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MedicalDashboard(BaseModel):
    total_children: int
    children_with_medical_profiles: int
    active_medications: int
    upcoming_vaccinations: int
    children_with_special_needs: int
    medical_visits_this_month: int
