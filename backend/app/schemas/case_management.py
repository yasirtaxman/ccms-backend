from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaseStatus(str, Enum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    CLOSED = "Closed"
    TRANSFERRED = "Transferred"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class WelfareStatus(str, Enum):
    STABLE = "Stable"
    NEEDS_ATTENTION = "Needs Attention"
    AT_RISK = "At Risk"
    CRITICAL = "Critical"


class NoteType(str, Enum):
    GENERAL = "General"
    HOME_VISIT = "Home Visit"
    FAMILY_CONTACT = "Family Contact"
    SCHOOL_CONTACT = "School Contact"
    MEDICAL_FOLLOW_UP = "Medical Follow-up"
    COUNSELING = "Counseling"
    BEHAVIOR = "Behavior"
    LEGAL = "Legal"
    EMERGENCY = "Emergency"


class NoteVisibility(str, Enum):
    NORMAL = "Normal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


class SessionType(str, Enum):
    INDIVIDUAL = "Individual"
    GROUP = "Group"
    FAMILY = "Family"
    EMERGENCY = "Emergency"


class SessionStatus(str, Enum):
    COMPLETED = "Completed"
    SCHEDULED = "Scheduled"
    CANCELLED = "Cancelled"


class IncidentType(str, Enum):
    BEHAVIORAL = "Behavioral"
    SAFETY = "Safety"
    HEALTH = "Health"
    DISCIPLINE = "Discipline"
    PROTECTION = "Protection"
    MISSING = "Missing"
    CONFLICT = "Conflict"
    OTHER = "Other"


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class IncidentReviewStatus(str, Enum):
    PENDING = "Pending Review"
    REVIEWED = "Reviewed"
    CLOSED = "Closed"


class GoalArea(str, Enum):
    EDUCATION = "Education"
    HEALTH = "Health"
    BEHAVIOR = "Behavior"
    EMOTIONAL_SUPPORT = "Emotional Support"
    FAMILY_REUNIFICATION = "Family Reunification"
    LEGAL = "Legal"
    LIFE_SKILLS = "Life Skills"
    GENERAL_WELFARE = "General Welfare"


class CarePlanStatus(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    CANCELLED = "Cancelled"


class ReviewType(str, Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUAL = "Annual"
    SPECIAL = "Special"
    EMERGENCY = "Emergency"


class ReviewStatus(str, Enum):
    COMPLETED = "Completed"
    PENDING = "Pending"
    CANCELLED = "Cancelled"


class TrackedResponse(BaseModel):
    id: int
    organization_id: int | None
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    deleted_by: int | None
    model_config = ConfigDict(from_attributes=True)


class ChildCaseProfileCreate(BaseModel):
    case_number: str = Field(min_length=1, max_length=50, examples=["CASE-0001"])
    case_opened_date: date
    case_status: CaseStatus = CaseStatus.OPEN
    risk_level: RiskLevel = RiskLevel.LOW
    welfare_status: WelfareStatus = WelfareStatus.STABLE
    assigned_case_worker: str | None = Field(default=None, max_length=255)
    case_summary: str | None = None
    family_background: str | None = None
    psychosocial_summary: str | None = None
    current_concerns: str | None = None
    care_plan_summary: str | None = None
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{
        "case_number": "CASE-0001", "case_opened_date": "2026-06-21",
        "case_status": "Open", "risk_level": "Medium", "welfare_status": "Stable",
        "assigned_case_worker": "Social Worker A"
    }]})


class ChildCaseProfileUpdate(BaseModel):
    case_number: str | None = Field(default=None, min_length=1, max_length=50)
    case_opened_date: date | None = None
    case_status: CaseStatus | None = None
    risk_level: RiskLevel | None = None
    welfare_status: WelfareStatus | None = None
    assigned_case_worker: str | None = Field(default=None, max_length=255)
    case_summary: str | None = None
    family_background: str | None = None
    psychosocial_summary: str | None = None
    current_concerns: str | None = None
    care_plan_summary: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"case_number", "case_opened_date", "case_status", "risk_level", "welfare_status"} & self.model_fields_set:
            if getattr(self, name) is None: raise ValueError(f"{name} cannot be null")
        return self


class ChildCaseProfileResponse(TrackedResponse, ChildCaseProfileCreate):
    child_id: int


class CaseNoteCreate(BaseModel):
    case_profile_id: int | None = Field(default=None, gt=0)
    note_date: date
    note_type: NoteType
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    visibility: NoteVisibility = NoteVisibility.NORMAL
    follow_up_required: bool = False
    follow_up_date: date | None = None
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{
        "note_date": "2026-06-21", "note_type": "Home Visit", "title": "Home visit",
        "description": "Child and guardian were interviewed.", "visibility": "Normal",
        "follow_up_required": True, "follow_up_date": "2026-06-28"
    }]})

    @model_validator(mode="after")
    def validate_follow_up(self):
        if self.follow_up_date is not None and self.follow_up_date < self.note_date:
            raise ValueError("follow_up_date cannot be before note_date")
        if self.follow_up_required and self.follow_up_date is None:
            raise ValueError("follow_up_date is required when follow_up_required is true")
        return self


class CaseNoteUpdate(BaseModel):
    note_date: date | None = None
    note_type: NoteType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    visibility: NoteVisibility | None = None
    follow_up_required: bool | None = None
    follow_up_date: date | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        required = {"note_date", "note_type", "title", "description", "visibility", "follow_up_required"}
        for name in required & self.model_fields_set:
            if getattr(self, name) is None: raise ValueError(f"{name} cannot be null")
        return self


class CaseNoteResponse(TrackedResponse, CaseNoteCreate):
    child_id: int


class CounselingSessionCreate(BaseModel):
    session_date: date
    counselor_name: str = Field(min_length=2, max_length=255)
    session_type: SessionType
    session_summary: str | None = None
    observations: str | None = None
    recommendations: str | None = None
    next_session_date: date | None = None
    status: SessionStatus
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{
        "session_date": "2026-06-21", "counselor_name": "Counselor A",
        "session_type": "Individual", "session_summary": "Initial support session",
        "next_session_date": "2026-06-28", "status": "Completed"
    }]})

    @model_validator(mode="after")
    def validate_dates(self):
        if self.next_session_date is not None and self.next_session_date < self.session_date:
            raise ValueError("next_session_date cannot be before session_date")
        return self


class CounselingSessionUpdate(BaseModel):
    session_date: date | None = None
    counselor_name: str | None = Field(default=None, min_length=2, max_length=255)
    session_type: SessionType | None = None
    session_summary: str | None = None
    observations: str | None = None
    recommendations: str | None = None
    next_session_date: date | None = None
    status: SessionStatus | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"session_date", "counselor_name", "session_type", "status"} & self.model_fields_set:
            if getattr(self, name) is None: raise ValueError(f"{name} cannot be null")
        return self


class CounselingSessionResponse(TrackedResponse, CounselingSessionCreate):
    child_id: int


class IncidentRecordCreate(BaseModel):
    incident_date: date
    incident_type: IncidentType
    severity: Severity
    location: str | None = Field(default=None, max_length=255)
    description: str = Field(min_length=1)
    immediate_action_taken: str | None = None
    reported_by: str = Field(min_length=2, max_length=255)
    review_status: IncidentReviewStatus = IncidentReviewStatus.PENDING
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{
        "incident_date": "2026-06-21", "incident_type": "Safety", "severity": "High",
        "location": "Play area", "description": "Safety incident requiring review.",
        "reported_by": "Case Worker", "review_status": "Pending Review"
    }]})


class IncidentRecordUpdate(BaseModel):
    incident_date: date | None = None
    incident_type: IncidentType | None = None
    severity: Severity | None = None
    location: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    immediate_action_taken: str | None = None
    reported_by: str | None = Field(default=None, min_length=2, max_length=255)
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"incident_date", "incident_type", "severity", "description", "reported_by"} & self.model_fields_set:
            if getattr(self, name) is None: raise ValueError(f"{name} cannot be null")
        return self


class IncidentRecordResponse(TrackedResponse, IncidentRecordCreate):
    child_id: int
    reviewed_by: int | None
    reviewed_at: date | None


class IncidentReviewRequest(BaseModel):
    reviewed_at: date | None = None
    model_config = ConfigDict(extra="forbid")


class CarePlanCreate(BaseModel):
    case_profile_id: int | None = Field(default=None, gt=0)
    plan_title: str = Field(min_length=1, max_length=255)
    plan_start_date: date
    plan_end_date: date | None = None
    goal_area: GoalArea
    goals: str = Field(min_length=1)
    planned_actions: str | None = None
    responsible_person: str | None = Field(default=None, max_length=255)
    status: CarePlanStatus = CarePlanStatus.ACTIVE
    progress_notes: str | None = None
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{
        "plan_title": "Education support", "plan_start_date": "2026-06-21",
        "goal_area": "Education", "goals": "Improve attendance and performance",
        "responsible_person": "Case Worker", "status": "Active"
    }]})

    @model_validator(mode="after")
    def validate_dates(self):
        if self.plan_end_date is not None and self.plan_end_date < self.plan_start_date:
            raise ValueError("plan_end_date cannot be before plan_start_date")
        return self


class CarePlanUpdate(BaseModel):
    plan_title: str | None = Field(default=None, min_length=1, max_length=255)
    plan_start_date: date | None = None
    plan_end_date: date | None = None
    goal_area: GoalArea | None = None
    goals: str | None = Field(default=None, min_length=1)
    planned_actions: str | None = None
    responsible_person: str | None = Field(default=None, max_length=255)
    status: CarePlanStatus | None = None
    progress_notes: str | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"plan_title", "plan_start_date", "goal_area", "goals", "status"} & self.model_fields_set:
            if getattr(self, name) is None: raise ValueError(f"{name} cannot be null")
        return self


class CarePlanResponse(TrackedResponse, CarePlanCreate):
    child_id: int


class CaseReviewCreate(BaseModel):
    case_profile_id: int | None = Field(default=None, gt=0)
    review_date: date
    review_type: ReviewType
    participants: str | None = None
    summary: str | None = None
    decisions: str | None = None
    next_review_date: date | None = None
    status: ReviewStatus
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{
        "review_date": "2026-06-21", "review_type": "Monthly",
        "participants": "Case worker, guardian", "summary": "Monthly welfare review",
        "next_review_date": "2026-07-21", "status": "Completed"
    }]})

    @model_validator(mode="after")
    def validate_dates(self):
        if self.next_review_date is not None and self.next_review_date < self.review_date:
            raise ValueError("next_review_date cannot be before review_date")
        return self


class CaseReviewUpdate(BaseModel):
    review_date: date | None = None
    review_type: ReviewType | None = None
    participants: str | None = None
    summary: str | None = None
    decisions: str | None = None
    next_review_date: date | None = None
    status: ReviewStatus | None = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def prevent_null_required_fields(self):
        for name in {"review_date", "review_type", "status"} & self.model_fields_set:
            if getattr(self, name) is None: raise ValueError(f"{name} cannot be null")
        return self


class CaseReviewResponse(TrackedResponse, CaseReviewCreate):
    child_id: int


class CaseDashboardResponse(BaseModel):
    total_case_profiles: int
    open_cases: int
    closed_cases: int
    high_risk_children: int
    critical_risk_children: int
    pending_follow_ups: int
    upcoming_case_reviews: int
    upcoming_counseling_sessions: int
    critical_incidents: int
    pending_incident_reviews: int
    active_care_plans: int
    children_without_case_profile: int
