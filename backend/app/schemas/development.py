from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Frequency = Literal["Monthly", "Weekly", "As Needed", "Incident Based", "Counselor Review", "Teacher Review", "Warden Review"]
ReviewStatus = Literal["Draft", "Submitted", "Reviewed", "Needs Follow-up", "Closed", "Archived"]
InputType = Literal["checkbox", "dropdown", "rating_1_to_5", "yes_no", "multi_select", "short_note"]
AITrendStatus = Literal["Improving", "Stable", "Needs Attention", "Mixed", "Not Enough Data"]
AIAttentionLevel = Literal["Low", "Moderate", "High", "Urgent Review"]
AIApprovalStatus = Literal["Draft", "Generated", "Reviewed", "Approved", "Rejected", "Archived"]
SupportPlanType = Literal["Behavior Support", "Emotional Support", "Learning Support", "Social Support", "Safety Support", "General Support"]
SupportPlanStatus = Literal["Draft", "Active", "Under Review", "Completed", "Closed", "Cancelled", "Archived"]
SupportPriority = Literal["Low", "Moderate", "High", "Urgent Review"]
SupportNoteType = Literal["Progress Note", "Staff Action", "Counselor Review", "Follow-up", "Incident Follow-up", "Closure Note"]


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

    @field_validator("input_type", mode="before")
    @classmethod
    def normalize_input_type(cls, value: str) -> str:
        if value == "rating":
            return "rating_1_to_5"
        return value


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


class DevelopmentAISummaryUpdate(BaseModel):
    overall_summary: str | None = None
    positive_strengths_summary: str | None = None
    support_needs_summary: str | None = None
    talent_interest_summary: str | None = None
    behavior_trend_summary: str | None = None
    emotional_wellbeing_summary: str | None = None
    learning_behavior_summary: str | None = None
    social_behavior_summary: str | None = None
    risk_attention_summary: str | None = None
    recommended_staff_actions: str | None = None
    recommended_counselor_actions: str | None = None
    next_review_date: date | None = None
    trend_status: AITrendStatus | None = None
    attention_level: AIAttentionLevel | None = None
    internal_notes: str | None = None
    is_sensitive: bool | None = None


class DevelopmentAISummaryReviewRequest(BaseModel):
    internal_notes: str | None = None


class DevelopmentAISummaryResponse(BaseModel):
    id: int
    child_id: int
    summary_period_month: int
    summary_period_year: int
    summary_type: str
    overall_summary: str | None
    positive_strengths_summary: str | None
    support_needs_summary: str | None
    talent_interest_summary: str | None
    behavior_trend_summary: str | None
    emotional_wellbeing_summary: str | None
    learning_behavior_summary: str | None
    social_behavior_summary: str | None
    risk_attention_summary: str | None
    recommended_staff_actions: str | None
    recommended_counselor_actions: str | None
    next_review_date: date | None
    trend_status: str
    attention_level: str
    approval_status: str
    generated_by_user_id: int | None
    reviewed_by_user_id: int | None
    approved_by_user_id: int | None
    generated_at: datetime
    reviewed_at: datetime | None
    approved_at: datetime | None
    source_observation_count: int
    source_date_from: date | None
    source_date_to: date | None
    is_ai_generated: bool
    is_sensitive: bool
    internal_notes: str | None = None
    created_at: datetime
    updated_at: datetime
    child_code: str | None = None
    child_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class BehaviorSupportPlanBase(BaseModel):
    plan_title: str = Field(min_length=2, max_length=255)
    plan_type: SupportPlanType = "Behavior Support"
    plan_status: SupportPlanStatus = "Draft"
    priority_level: SupportPriority = "Low"
    identified_behavior: str | None = None
    behavior_description: str | None = None
    possible_triggers: str | None = None
    known_patterns: str | None = None
    time_location_context: str | None = None
    replacement_positive_behavior: str | None = None
    prevention_strategies: str | None = None
    staff_response_plan: str | None = None
    de_escalation_steps: str | None = None
    positive_reinforcement_plan: str | None = None
    environment_adjustments: str | None = None
    communication_support: str | None = None
    learning_support: str | None = None
    social_support: str | None = None
    counselor_recommendations: str | None = None
    guardian_communication_notes: str | None = None
    start_date: date | None = None
    review_date: date | None = None
    end_date: date | None = None
    created_from_observation_id: int | None = None
    created_from_ai_summary_id: int | None = None
    responsible_staff_id: int | None = None
    counselor_id: int | None = None
    progress_summary: str | None = None
    review_outcome: str | None = None
    closure_reason: str | None = None
    is_sensitive: bool = False
    internal_notes: str | None = None


class BehaviorSupportPlanCreate(BehaviorSupportPlanBase):
    pass


class BehaviorSupportPlanUpdate(BaseModel):
    plan_title: str | None = Field(default=None, min_length=2, max_length=255)
    plan_type: SupportPlanType | None = None
    plan_status: SupportPlanStatus | None = None
    priority_level: SupportPriority | None = None
    identified_behavior: str | None = None
    behavior_description: str | None = None
    possible_triggers: str | None = None
    known_patterns: str | None = None
    time_location_context: str | None = None
    replacement_positive_behavior: str | None = None
    prevention_strategies: str | None = None
    staff_response_plan: str | None = None
    de_escalation_steps: str | None = None
    positive_reinforcement_plan: str | None = None
    environment_adjustments: str | None = None
    communication_support: str | None = None
    learning_support: str | None = None
    social_support: str | None = None
    counselor_recommendations: str | None = None
    guardian_communication_notes: str | None = None
    start_date: date | None = None
    review_date: date | None = None
    end_date: date | None = None
    responsible_staff_id: int | None = None
    counselor_id: int | None = None
    progress_summary: str | None = None
    review_outcome: str | None = None
    closure_reason: str | None = None
    is_sensitive: bool | None = None
    internal_notes: str | None = None


class BehaviorSupportPlanResponse(BehaviorSupportPlanBase):
    id: int
    child_id: int
    plan_code: str
    approved_by_user_id: int | None
    created_by_user_id: int
    updated_by_user_id: int
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    closed_at: datetime | None
    child_code: str | None = None
    child_name: str | None = None
    responsible_staff_name: str | None = None
    latest_progress_note: str | None = None
    model_config = ConfigDict(from_attributes=True)


class BehaviorSupportPlanNoteCreate(BaseModel):
    note_date: date
    note_type: SupportNoteType = "Progress Note"
    progress_note: str | None = None
    staff_action_taken: str | None = None
    child_response: str | None = None
    follow_up_required: bool = False
    next_step: str | None = None


class BehaviorSupportPlanNoteUpdate(BaseModel):
    note_date: date | None = None
    note_type: SupportNoteType | None = None
    progress_note: str | None = None
    staff_action_taken: str | None = None
    child_response: str | None = None
    follow_up_required: bool | None = None
    next_step: str | None = None


class BehaviorSupportPlanNoteResponse(BehaviorSupportPlanNoteCreate):
    id: int
    plan_id: int
    child_id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
