from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class SponsorType(str, Enum):
    INDIVIDUAL = "Individual"
    ORGANIZATION = "Organization"
    FOUNDATION = "Foundation"
    CORPORATE = "Corporate"


class SponsorStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BLOCKED = "Blocked"


class SponsorshipStatus(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    SUSPENDED = "Suspended"


class SponsorshipType(str, Enum):
    FULL = "Full"
    PARTIAL = "Partial"
    EDUCATION = "Education"
    MEDICAL = "Medical"
    GENERAL = "General"


MOBILE_PATTERN = r"^\+?[0-9][0-9 ()-]{6,28}$"


class SponsorCreate(BaseModel):
    sponsor_code: str = Field(min_length=2, max_length=50, examples=["SP-0001"])
    sponsor_type: SponsorType
    full_name: str = Field(min_length=2, max_length=255, examples=["Ayesha Khan"])
    organization_name: str | None = Field(default=None, max_length=255)
    mobile: str = Field(pattern=MOBILE_PATTERN, examples=["+92 300 1234567"])
    alternate_mobile: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    email: EmailStr | None = Field(default=None, examples=["sponsor@ccms.example"])
    cnic_passport: str | None = Field(default=None, max_length=50)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    province: str | None = Field(default=None, max_length=100)
    country: str = Field(default="Pakistan", min_length=2, max_length=100)
    occupation: str | None = Field(default=None, max_length=150)
    status: SponsorStatus = SponsorStatus.ACTIVE
    remarks: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("sponsor_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("full_name", "country")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return " ".join(value.split())


class SponsorUpdate(BaseModel):
    sponsor_code: str | None = Field(default=None, min_length=2, max_length=50)
    sponsor_type: SponsorType | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    organization_name: str | None = Field(default=None, max_length=255)
    mobile: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    alternate_mobile: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    email: EmailStr | None = None
    cnic_passport: str | None = Field(default=None, max_length=50)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    province: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    occupation: str | None = Field(default=None, max_length=150)
    status: SponsorStatus | None = None
    remarks: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("sponsor_code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        required = {"sponsor_code", "sponsor_type", "full_name", "mobile", "country", "status"}
        for field_name in required & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class SponsorResponse(BaseModel):
    id: int
    sponsor_code: str
    sponsor_type: SponsorType
    full_name: str
    organization_name: str | None
    mobile: str
    alternate_mobile: str | None
    email: EmailStr | None
    cnic_passport: str | None
    address: str | None
    city: str | None
    district: str | None
    province: str | None
    country: str
    occupation: str | None
    status: SponsorStatus
    remarks: str | None
    created_by: int
    updated_by: int
    deleted_at: datetime | None
    deleted_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChildSponsorshipCreate(BaseModel):
    sponsor_id: int = Field(gt=0)
    start_date: date
    end_date: date | None = None
    status: SponsorshipStatus = SponsorshipStatus.ACTIVE
    sponsorship_type: SponsorshipType
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ChildSponsorshipUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    status: SponsorshipStatus | None = None
    sponsorship_type: SponsorshipType | None = None
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        required = {"start_date", "status", "sponsorship_type"}
        for field_name in required & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class ChildSponsorshipResponse(BaseModel):
    id: int
    child_id: int
    sponsor_id: int
    start_date: date
    end_date: date | None
    status: SponsorshipStatus
    sponsorship_type: SponsorshipType
    notes: str | None
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SponsorSearchResponse(BaseModel):
    items: list[SponsorResponse | SponsorViewerResponse]
    total: int
    skip: int
    limit: int


class SponsoredChildResponse(BaseModel):
    sponsorship_id: int
    child_id: int
    child_code: str
    child_name: str
    start_date: date
    end_date: date | None
    status: SponsorshipStatus
    sponsorship_type: SponsorshipType


class ChildWithoutSponsorResponse(BaseModel):
    id: int
    child_id: str
    full_name: str
    status: str


class SponsorViewerResponse(BaseModel):
    """Sponsor representation that deliberately omits all sensitive contact data."""

    id: int
    sponsor_code: str
    sponsor_type: SponsorType
    full_name: str
    organization_name: str | None
    city: str | None
    district: str | None
    province: str | None
    country: str
    occupation: str | None
    status: SponsorStatus
    remarks: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


SponsorSearchResponse.model_rebuild()
