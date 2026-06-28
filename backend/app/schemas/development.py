from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Frequency = Literal["Monthly", "Weekly", "As Needed", "Incident Based", "Counselor Review", "Teacher Review", "Warden Review"]
ReviewStatus = Literal["Draft", "Submitted", "Reviewed", "Needs Follow-up", "Closed", "Archived"]
InputType = Literal["checkbox", "dropdown", "rating_1_to_5", "yes_no", "multi_select", "short_note"]


class DevelopmentIndicatorBase(BaseModel):
    indicator_name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=150)
    description: str | None = None
    input_type: InputType
    options_json: list[Any] | dict[str, Any] | None = None
    is_required: bool = False
    is_active: bool = True
    is_sensitive: bool = False
    sort_order: int = 0


class DevelopmentIndicatorCreate(DevelopmentIndicatorBase):
    indicator_code: str = Field(min_length=2, max_length=80)

    @field_validator("indicator_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "_")


class DevelopmentIndicatorUpdate(BaseModel):
    indicator_name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    options_json: list[Any] | dict[str, Any] | None = None
    is_required: bool | None = None
    is_sensitive: bool | None = None
    sort_order: int | None = None


class DevelopmentIndicatorResponse(DevelopmentIndicatorBase):
    id: int
    indicator_code: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ObservationResponseInput(BaseModel):
    indicator_id: int
    value_text: str | None = None
    value_number: int | None = None
    value_boolean: bool | None = None
    value_json: list[Any] | dict[str, Any] | None = None
    note: str | None = None


class ObservationResponseOutput(ObservationResponseInput):
    id: int
    indicator: DevelopmentIndicatorResponse | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ObservationBase(BaseModel):
    child_id: int
    observation_date: date
    observation_period_start: date | None = None
    observation_period_end: date | None = None
    observation_frequency: Frequency
    observer_role: str | None = None
    review_status: ReviewStatus = "Draft"
    next_review_date: date | None = None
    general_summary: str | None = None
    recommended_support: str | None = None
    private_notes: str | None = None
    responses: list[ObservationResponseInput] = Field(default_factory=list)


class ObservationCreate(ObservationBase):
    pass


class ObservationUpdate(BaseModel):
    observation_date: date | None = None
    observation_period_start: date | None = None
    observation_period_end: date | None = None
    observation_frequency: Frequency | None = None
    observer_role: str | None = None
    next_review_date: date | None = None
    general_summary: str | None = None
    recommended_support: str | None = None
    private_notes: str | None = None
    responses: list[ObservationResponseInput] | None = None


class ObservationReviewRequest(BaseModel):
    recommended_support: str | None = None
    next_review_date: date | None = None
    review_status: Literal["Reviewed", "Needs Follow-up"] = "Reviewed"


class ObservationResponse(BaseModel):
    id: int
    child_id: int
    observation_date: date
    observation_period_start: date | None
    observation_period_end: date | None
    observation_frequency: str
    observed_by_user_id: int | None
    observer_role: str | None
    review_status: str
    general_summary: str | None
    recommended_support: str | None
    private_notes: str | None = None
    urgent_flag: bool
    next_review_date: date | None
    submitted_at: datetime | None
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    updated_by_user_id: int
    responses: list[ObservationResponseOutput] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class DevelopmentSummary(BaseModel):
    child_id: int
    latest_observation_date: date | None
    review_status: str
    monthly_review_status: str
    positive_strengths: list[str]
    strongest_positive_strengths: list[str]
    support_needs: list[str]
    possible_areas_of_interest: list[str]
    talent_indicators: list[str]
    recommended_support: str
    risk_flags_requiring_review: list[str]
    next_review_date: date | None
    summary_text: str
    urgent_flag_safe_summary: str
    observation_count: int
