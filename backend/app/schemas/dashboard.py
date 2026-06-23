from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChildrenSummary(StrictModel):
    total_children: int
    active_children: int
    inactive_children: int
    discharged_children: int
    transferred_children: int
    children_admitted_today: int
    children_admitted_this_week: int
    children_admitted_this_month: int
    children_without_case_profile: int
    children_without_medical_profile: int
    children_without_education_record: int
    children_without_bed: int
    children_without_active_sponsor: int


class SponsorshipSummary(StrictModel):
    total_sponsors: int
    active_sponsors: int
    inactive_sponsors: int
    active_sponsorships: int
    expired_sponsorships: int
    sponsorships_expiring_30_days: int
    children_with_active_sponsor: int
    children_without_active_sponsor: int


class AccommodationSummary(StrictModel):
    total_buildings: int
    total_blocks: int
    total_floors: int
    total_rooms: int
    total_beds: int
    occupied_beds: int
    vacant_beds: int
    reserved_beds: int
    maintenance_beds: int
    occupancy_percentage: float


class MedicalSummary(StrictModel):
    children_with_medical_profiles: int
    children_without_medical_profile: int
    active_medications: int
    upcoming_vaccinations_30_days: int
    medical_visits_this_month: int
    children_with_special_needs: int
    children_with_chronic_diseases: int


class EducationSummary(StrictModel):
    active_students: int
    schools_count: int
    average_attendance: float
    average_marks: float
    board_exam_students: int
    low_attendance_students: int
    dropout_students: int


class CaseManagementSummary(StrictModel):
    total_case_profiles: int
    open_cases: int
    closed_cases: int
    high_risk_children: int
    critical_risk_children: int
    pending_follow_ups: int
    upcoming_case_reviews_30_days: int
    upcoming_counseling_sessions_30_days: int
    critical_incidents: int
    pending_incident_reviews: int
    active_care_plans: int


class DocumentSummary(StrictModel):
    total_documents: int
    verified_documents: int
    unverified_documents: int
    children_with_complete_admission_documents: int
    children_with_incomplete_admission_documents: int


class AlertsSummary(StrictModel):
    critical_incidents: int
    critical_risk_children: int
    upcoming_vaccinations: int
    active_medications: int
    pending_follow_ups: int
    pending_incident_reviews: int
    children_without_beds: int
    children_without_active_sponsors: int
    children_without_medical_profiles: int
    children_without_case_profiles: int


class PendingActionsSummary(StrictModel):
    documents_pending_verification: int
    incidents_pending_review: int
    follow_ups_due: int
    case_reviews_due: int
    vaccinations_due: int
    children_pending_bed_allocation: int
    children_pending_sponsorship: int


class ExecutiveDashboardResponse(StrictModel):
    children_summary: ChildrenSummary
    sponsorship_summary: SponsorshipSummary
    accommodation_summary: AccommodationSummary
    medical_summary: MedicalSummary
    education_summary: EducationSummary
    case_management_summary: CaseManagementSummary
    document_summary: DocumentSummary
    alerts_summary: AlertsSummary
    pending_actions_summary: PendingActionsSummary


class OperationalDashboardResponse(StrictModel):
    today_admissions: int
    this_week_admissions: int
    this_month_admissions: int
    pending_document_verifications: int
    vacant_beds: int
    occupied_beds: int
    children_without_beds: int
    active_sponsorships: int
    expiring_sponsorships_30_days: int
    upcoming_vaccinations_30_days: int
    upcoming_case_reviews_30_days: int
    upcoming_counseling_sessions_30_days: int
    active_medications: int
    pending_incident_reviews: int
    follow_ups_due: int
    low_attendance_children: int
    children_with_active_care_plans: int


class SafeAlertReference(StrictModel):
    module: str
    id: int
    child_id: int | None = None
    display_title: str
    status: str


class AlertGroup(StrictModel):
    counts: dict[str, int]
    references: dict[str, list[SafeAlertReference]] = Field(default_factory=dict)


class AlertsDashboardResponse(StrictModel):
    critical_alerts: AlertGroup
    warning_alerts: AlertGroup
    info_alerts: AlertGroup


class ChildCompleteProfileSummaryResponse(StrictModel):
    child_basic: dict
    admission_documents: dict
    sponsorship: dict
    accommodation: dict
    medical: dict
    education: dict
    case_management: dict
    daily_attendance: dict


class SearchResult(StrictModel):
    module: str
    id: int
    display_title: str
    display_subtitle: str | None = None
    status: str


class GlobalSearchResponse(StrictModel):
    query: str
    children: list[SearchResult]
    sponsors: list[SearchResult]
    education: list[SearchResult]
    accommodation: list[SearchResult]
    case_management: list[SearchResult]
