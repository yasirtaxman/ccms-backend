r"""Seed fictional CCMS demo data for local training and QA.

Run from the backend folder:
    $env:PYTHONPATH="."
    python .\scripts\seed_demo_data.py
"""
from __future__ import annotations

from datetime import date, time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.accommodation import Bed, BedAllocation, Block, Building, Floor, Room
from app.models.attendance import Attendance
from app.models.case_management import CarePlan, CaseNote, ChildCaseProfile
from app.models.child import Child
from app.models.child_attendance import DailyChildAttendance
from app.models.development import (
    ChildBehaviorSupportPlan,
    ChildBehaviorSupportPlanNote,
    ChildDevelopmentAISummary,
    ChildDevelopmentObservation,
    ChildDevelopmentObservationResponse,
    DevelopmentIndicator,
)
from app.models.document import Document
from app.models.education_record import EducationRecord
from app.models.medical_profile import MedicalProfile
from app.models.organization_profile import OrganizationProfile
from app.models.role import Role
from app.models.school import School
from app.models.sponsor import ChildSponsorship, Sponsor
from app.models.user import User
from app.models.visitor import ChildVisit, Visitor
from app.services.permission_service import DEFAULT_ROLE_PERMISSIONS, seed_permissions


DEMO_PASSWORD = "DemoUser123!"
ROLE_NAMES = ("Admin", "Manager", "Warden", "Data Entry Operator", "Viewer", "Counselor")


def first_by(db: Session, model, **filters):
    query = select(model)
    for field, value in filters.items():
        query = query.where(getattr(model, field) == value)
    return db.scalar(query)


def update_fields(instance, **values):
    for field, value in values.items():
        setattr(instance, field, value)
    return instance


def ensure_roles(db: Session) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for name in ROLE_NAMES:
        role = first_by(db, Role, name=name)
        if role is None:
            role = Role(name=name, is_system=name in DEFAULT_ROLE_PERMISSIONS)
            db.add(role)
            db.flush()
        roles[name] = role
    seed_permissions(db)
    return roles


def ensure_user(db: Session, username: str, full_name: str, role: Role) -> User:
    user = first_by(db, User, username=username)
    email = {
        "demo_admin": "admin@example.com",
        "demo_manager": "manager@example.com",
        "demo_warden": "warden@example.com",
        "demo_viewer": "viewer@example.com",
    }.get(username, f"{username}@example.com")
    if user is None:
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            is_active=True,
            force_password_change=True,
        )
        db.add(user)
        db.flush()
    else:
        update_fields(user, full_name=full_name, email=email, is_active=True)
    if role not in user.roles:
        user.roles.append(role)
    return user


def seed_organization(db: Session) -> OrganizationProfile:
    organization = first_by(db, OrganizationProfile, short_name="CCMS-DEMO")
    if organization is None:
        organization = OrganizationProfile(
            organization_name="CCMS Demo Child Care Center",
            short_name="CCMS-DEMO",
            address="Demo Street, Training Area",
            city="Demo City",
            district="Demo District",
            province="Demo Province",
            country="Pakistan",
            phone="03000000000",
            email="info@demo.ccms.local",
            website="https://demo.ccms.local",
            registration_no="DEMO-REG-0001",
            report_footer_text="Generated from fictional CCMS demo data.",
            report_watermark_text="CCMS DEMO",
            primary_color="#2563eb",
            secondary_color="#0f172a",
            authorized_signatory_name="Demo Administrator",
            authorized_signatory_designation="Program Director",
            is_active=True,
        )
        db.add(organization)
    else:
        update_fields(
            organization,
            organization_name="CCMS Demo Child Care Center",
            is_active=True,
            report_footer_text="Generated from fictional CCMS demo data.",
            report_watermark_text="CCMS DEMO",
        )
    return organization


def seed_children(db: Session) -> list[Child]:
    child_rows = [
        {
            "child_id": "DEMO-CH-0001",
            "admission_file_no": "DEMO-AF-0001",
            "full_name": "Demo Child One",
            "father_name": "Demo Father One",
            "grandfather_name": "Demo Grandfather One",
            "mother_name": "Demo Mother One",
            "gender": "Male",
            "date_of_birth": date(2014, 5, 15),
            "guardian_name": "Demo Guardian One",
            "guardian_relationship": "Uncle",
            "guardian_cnic": "00000-0000000-0",
            "guardian_mobile": "03000000001",
            "current_address": "Demo House 1, Training Area",
            "permanent_address": "Demo Village 1, Training Area",
            "village_mohallah": "Demo Mohallah",
            "union_council": "Demo Council",
            "tehsil": "Demo Tehsil",
            "district": "Demo District",
            "province": "Demo Province",
            "admission_date": date(2026, 1, 10),
            "reason_for_admission": "Fictional local demo record for staff training.",
            "status": "Active",
        },
        {
            "child_id": "DEMO-CH-0002",
            "admission_file_no": "DEMO-AF-0002",
            "full_name": "Demo Child Two",
            "father_name": "Demo Father Two",
            "grandfather_name": "Demo Grandfather Two",
            "mother_name": "Demo Mother Two",
            "gender": "Female",
            "date_of_birth": date(2016, 8, 22),
            "guardian_name": "Demo Guardian Two",
            "guardian_relationship": "Aunt",
            "guardian_cnic": "00000-0000000-1",
            "guardian_mobile": "03000000002",
            "current_address": "Demo House 2, Training Area",
            "permanent_address": "Demo Village 2, Training Area",
            "village_mohallah": "Demo Mohallah",
            "union_council": "Demo Council",
            "tehsil": "Demo Tehsil",
            "district": "Demo District",
            "province": "Demo Province",
            "admission_date": date(2026, 2, 5),
            "reason_for_admission": "Fictional local demo record for staff training.",
            "status": "Active",
        },
    ]
    children: list[Child] = []
    for row in child_rows:
        child = first_by(db, Child, child_id=row["child_id"])
        if child is None:
            child = Child(**row)
            db.add(child)
            db.flush()
        else:
            update_fields(child, **row)
        children.append(child)
    return children


def seed_accommodation(db: Session, admin: User, children: list[Child]) -> None:
    building = first_by(db, Building, building_code="DEMO-BLD-A")
    if building is None:
        building = Building(
            building_code="DEMO-BLD-A",
            building_name="Demo Residence A",
            description="Fictional accommodation block for local demo use.",
            gender_type="Mixed",
            status="Active",
            created_by=admin.id,
            updated_by=admin.id,
        )
        db.add(building)
        db.flush()

    block = first_by(db, Block, building_id=building.id, block_code="DEMO-BLK-1")
    if block is None:
        block = Block(building_id=building.id, block_code="DEMO-BLK-1", block_name="Demo Block 1", status="Active", created_by=admin.id, updated_by=admin.id)
        db.add(block)
        db.flush()

    floor = first_by(db, Floor, block_id=block.id, floor_no=1)
    if floor is None:
        floor = Floor(block_id=block.id, floor_no=1, floor_name="Ground Floor", status="Active", created_by=admin.id, updated_by=admin.id)
        db.add(floor)
        db.flush()

    room = first_by(db, Room, room_code="DEMO-RM-101")
    if room is None:
        room = Room(floor_id=floor.id, room_code="DEMO-RM-101", room_name="Demo Room 101", capacity=4, gender_type="Mixed", status="Active", created_by=admin.id, updated_by=admin.id)
        db.add(room)
        db.flush()

    for index, child in enumerate(children, start=1):
        bed_code = f"DEMO-BED-10{index}"
        bed = first_by(db, Bed, bed_code=bed_code)
        if bed is None:
            bed = Bed(room_id=room.id, bed_code=bed_code, bed_name=f"Demo Bed {index}", status="Occupied", created_by=admin.id, updated_by=admin.id)
            db.add(bed)
            db.flush()
        allocation = first_by(db, BedAllocation, child_id=child.id, status="Active")
        if allocation is None:
            db.add(
                BedAllocation(
                    child_id=child.id,
                    bed_id=bed.id,
                    allocation_date=child.admission_date,
                    allocation_reason="Demo initial allocation",
                    status="Active",
                    notes="Fictional demo allocation.",
                    created_by=admin.id,
                    updated_by=admin.id,
                )
            )


def seed_child_supporting_records(db: Session, admin: User, children: list[Child]) -> None:
    for child in children:
        if first_by(db, DailyChildAttendance, child_id=child.id, attendance_date=date(2026, 6, 20)) is None:
            db.add(
                DailyChildAttendance(
                    child_id=child.id,
                    attendance_date=date(2026, 6, 20),
                    status="Present",
                    check_in_time=time(8, 0),
                    check_out_time=time(17, 0),
                    marked_by=admin.id,
                    remarks="Demo attendance record.",
                    created_by=admin.id,
                    updated_by=admin.id,
                )
            )

        if first_by(db, Document, child_id=child.id, document_type="Admission Form") is None:
            db.add(
                Document(
                    child_id=child.id,
                    document_type="Admission Form",
                    original_filename=f"{child.child_id}_admission_form.pdf",
                    stored_filename=f"{child.child_id}_admission_form_demo.pdf",
                    file_path=f"uploads/demo/{child.child_id}_admission_form_demo.pdf",
                    is_verified=True,
                )
            )

        if first_by(db, MedicalProfile, child_id=child.id) is None:
            db.add(
                MedicalProfile(
                    child_id=child.id,
                    blood_group="O+",
                    allergies="None reported in demo data.",
                    chronic_diseases="None reported in demo data.",
                    disabilities="None reported in demo data.",
                    special_needs="Routine staff monitoring.",
                    height_cm=Decimal("135.00"),
                    weight_kg=Decimal("31.50"),
                    emergency_notes="Use local emergency protocol during demo.",
                    created_by=admin.id,
                    updated_by=admin.id,
                )
            )


def seed_education(db: Session, admin: User, children: list[Child]) -> None:
    school = first_by(db, School, school_code="DEMO-SCH-001")
    if school is None:
        school = School(
            school_code="DEMO-SCH-001",
            school_name="CCMS Demo Learning Center",
            school_type="Private",
            address="Demo Education Street",
            city="Demo City",
            district="Demo District",
            province="Demo Province",
            contact_person="Demo Education Coordinator",
            phone="03000000003",
            email="demo.school@ccms.org",
            status="Active",
            created_by=admin.id,
            updated_by=admin.id,
        )
        db.add(school)
        db.flush()
    else:
        school.email = "demo.school@ccms.org"

    for index, child in enumerate(children, start=1):
        record = first_by(db, EducationRecord, child_id=child.id, status="Studying")
        if record is None:
            record = EducationRecord(
                child_id=child.id,
                school_id=school.id,
                admission_number=f"DEMO-SCH-ADM-{index:04d}",
                class_level=f"Grade {index + 3}",
                academic_year="2026",
                start_date=date(2026, 3, 1),
                status="Studying",
                remarks="Demo education enrollment.",
                created_by=admin.id,
                updated_by=admin.id,
            )
            db.add(record)
            db.flush()
        if first_by(db, Attendance, education_record_id=record.id, month=6, year=2026) is None:
            db.add(
                Attendance(
                    education_record_id=record.id,
                    month=6,
                    year=2026,
                    total_days=20,
                    present_days=18,
                    absent_days=2,
                    attendance_percentage=Decimal("90.00"),
                    remarks="Demo education attendance.",
                    created_by=admin.id,
                    updated_by=admin.id,
                )
            )


def seed_case_management(db: Session, admin: User, children: list[Child]) -> None:
    for index, child in enumerate(children, start=1):
        profile = first_by(db, ChildCaseProfile, child_id=child.id)
        if profile is None:
            profile = ChildCaseProfile(
                child_id=child.id,
                case_number=f"DEMO-CASE-{index:04d}",
                case_opened_date=child.admission_date,
                case_status="Open",
                risk_level="Low",
                welfare_status="Stable",
                assigned_case_worker="Demo Case Worker",
                case_summary="Fictional case profile for local training.",
                family_background="Demo background information.",
                current_concerns="Routine follow-up only in demo data.",
                care_plan_summary="Continue education, care, and staff check-ins.",
                created_by=admin.id,
                updated_by=admin.id,
            )
            db.add(profile)
            db.flush()
        if first_by(db, CaseNote, child_id=child.id, title="Demo intake follow-up") is None:
            db.add(
                CaseNote(
                    child_id=child.id,
                    case_profile_id=profile.id,
                    note_date=date(2026, 6, 15),
                    note_type="General",
                    title="Demo intake follow-up",
                    description="Staff completed a fictional follow-up for training.",
                    visibility="Normal",
                    follow_up_required=True,
                    follow_up_date=date(2026, 7, 15),
                    created_by=admin.id,
                    updated_by=admin.id,
                )
            )
        if first_by(db, CarePlan, child_id=child.id, plan_title="Demo education support plan") is None:
            db.add(
                CarePlan(
                    child_id=child.id,
                    case_profile_id=profile.id,
                    plan_title="Demo education support plan",
                    plan_start_date=date(2026, 6, 1),
                    goal_area="Education",
                    goals="Maintain regular class participation.",
                    planned_actions="Weekly progress check by assigned staff.",
                    responsible_person="Demo Case Worker",
                    status="Active",
                    progress_notes="Initial demo plan created.",
                    created_by=admin.id,
                    updated_by=admin.id,
                )
            )


def seed_sponsorship_and_visits(db: Session, admin: User, children: list[Child]) -> None:
    sponsor = first_by(db, Sponsor, sponsor_code="DEMO-SP-001")
    if sponsor is None:
        sponsor = Sponsor(
            sponsor_code="DEMO-SP-001",
            sponsor_type="Individual",
            full_name="Demo Sponsor",
            mobile="03000000004",
            email="demo.sponsor@ccms.org",
            cnic_passport="DEMO-PASSPORT-001",
            address="Demo Sponsor Address",
            city="Demo City",
            district="Demo District",
            province="Demo Province",
            country="Pakistan",
            occupation="Demo Professional",
            status="Active",
            remarks="Fictional sponsor record.",
            created_by=admin.id,
            updated_by=admin.id,
        )
        db.add(sponsor)
        db.flush()
    else:
        sponsor.email = "demo.sponsor@ccms.org"
    for child in children:
        if first_by(db, ChildSponsorship, child_id=child.id, sponsor_id=sponsor.id) is None:
            db.add(
                ChildSponsorship(
                    child_id=child.id,
                    sponsor_id=sponsor.id,
                    start_date=date(2026, 6, 1),
                    status="Active",
                    sponsorship_type="Education",
                    notes="Fictional sponsorship for demo reporting.",
                    created_by=admin.id,
                    updated_by=admin.id,
                )
            )

    visitor = first_by(db, Visitor, visitor_code="DEMO-VIS-001")
    if visitor is None:
        visitor = Visitor(
            visitor_code="DEMO-VIS-001",
            full_name="Demo Approved Visitor",
            father_name="Demo Visitor Father",
            cnic_passport="DEMO-VISITOR-ID-001",
            mobile="03000000005",
            relationship_to_child="Uncle",
            address="Demo Visitor Address",
            district="Demo District",
            province="Demo Province",
            is_verified=True,
            verification_method="Demo verification",
            verified_by_user_id=admin.id,
            status="Active",
            remarks="Fictional visitor record.",
            created_by_user_id=admin.id,
            updated_by_user_id=admin.id,
        )
        db.add(visitor)
        db.flush()
    child = children[0]
    if first_by(db, ChildVisit, visit_code="DEMO-VST-001") is None:
        db.add(
            ChildVisit(
                visit_code="DEMO-VST-001",
                child_id=child.id,
                visitor_id=visitor.id,
                relationship_to_child="Uncle",
                visit_date=date(2026, 6, 25),
                check_in_time=time(10, 0),
                check_out_time=time(11, 0),
                meeting_purpose="Family contact",
                meeting_location="Visitor Room",
                supervised_by_user_id=admin.id,
                approved_by_user_id=admin.id,
                approval_status="Approved",
                visit_status="Completed",
                remarks="Fictional completed child visit.",
                safety_notes="No concerns recorded in demo data.",
                created_by_user_id=admin.id,
                updated_by_user_id=admin.id,
            )
        )


def seed_development(db: Session, admin: User, children: list[Child]) -> None:
    indicator = first_by(db, DevelopmentIndicator, indicator_code="DEMO-SOCIAL-PARTICIPATION")
    if indicator is None:
        indicator = DevelopmentIndicator(
            indicator_code="DEMO-SOCIAL-PARTICIPATION",
            indicator_name="Social Participation",
            category="Social Skills",
            description="Tracks safe, observable participation with peers.",
            input_type="rating_1_to_5",
            options_json=["1 Poor", "2 Needs Improvement", "3 Satisfactory", "4 Good", "5 Excellent"],
            is_required=True,
            sort_order=10,
        )
        db.add(indicator)
        db.flush()
    else:
        indicator.input_type = "rating_1_to_5"
        indicator.options_json = ["1 Poor", "2 Needs Improvement", "3 Satisfactory", "4 Good", "5 Excellent"]

    child = children[0]
    observation = first_by(db, ChildDevelopmentObservation, child_id=child.id, observation_date=date(2026, 6, 20))
    if observation is None:
        observation = ChildDevelopmentObservation(
            child_id=child.id,
            observation_date=date(2026, 6, 20),
            observation_period_start=date(2026, 6, 1),
            observation_period_end=date(2026, 6, 20),
            observation_frequency="Monthly",
            observed_by_user_id=admin.id,
            observer_role="Demo Staff",
            review_status="Submitted",
            general_summary="Child participated well in structured group activities.",
            recommended_support="Continue encouragement through supervised group tasks.",
            urgent_flag=False,
            next_review_date=date(2026, 7, 20),
            created_by_user_id=admin.id,
            updated_by_user_id=admin.id,
        )
        db.add(observation)
        db.flush()
    if first_by(db, ChildDevelopmentObservationResponse, observation_id=observation.id, indicator_id=indicator.id) is None:
        db.add(
            ChildDevelopmentObservationResponse(
                observation_id=observation.id,
                indicator_id=indicator.id,
                value_text="Strong",
                note="Fictional observation response for demo use.",
            )
        )
    summary = first_by(db, ChildDevelopmentAISummary, child_id=child.id, summary_period_month=6, summary_period_year=2026)
    if summary is None:
        summary = ChildDevelopmentAISummary(
            child_id=child.id,
            summary_period_month=6,
            summary_period_year=2026,
            overall_summary="Demo summary based on staff observations.",
            positive_strengths_summary="Shows interest in teamwork and learning routines.",
            support_needs_summary="Benefits from predictable daily structure.",
            talent_interest_summary="Enjoys drawing and group reading.",
            behavior_trend_summary="Stable participation pattern in demo data.",
            recommended_staff_actions="Use clear instructions and positive reinforcement.",
            next_review_date=date(2026, 7, 20),
            trend_status="Stable",
            attention_level="Low",
            approval_status="Generated",
            generated_by_user_id=admin.id,
            source_observation_count=1,
            source_date_from=date(2026, 6, 1),
            source_date_to=date(2026, 6, 20),
            is_ai_generated=False,
        )
        db.add(summary)
        db.flush()
    plan = first_by(db, ChildBehaviorSupportPlan, plan_code="DEMO-BSP-0001")
    if plan is None:
        plan = ChildBehaviorSupportPlan(
            child_id=child.id,
            plan_code="DEMO-BSP-0001",
            plan_title="Demo positive routine support",
            plan_type="Routine Support",
            plan_status="Active",
            priority_level="Low",
            identified_behavior="Needs reminders during transitions.",
            behavior_description="Occasional hesitation when moving between activities.",
            possible_triggers="Unexpected schedule changes.",
            replacement_positive_behavior="Ask staff for the next step.",
            prevention_strategies="Preview the daily schedule each morning.",
            staff_response_plan="Use calm prompts and clear choices.",
            positive_reinforcement_plan="Praise successful transitions.",
            start_date=date(2026, 6, 20),
            review_date=date(2026, 7, 20),
            responsible_staff_id=admin.id,
            progress_summary="Initial demo support plan.",
            created_by_user_id=admin.id,
            updated_by_user_id=admin.id,
        )
        db.add(plan)
        db.flush()
    if first_by(db, ChildBehaviorSupportPlanNote, plan_id=plan.id, note_date=date(2026, 6, 25)) is None:
        db.add(
            ChildBehaviorSupportPlanNote(
                plan_id=plan.id,
                child_id=child.id,
                note_date=date(2026, 6, 25),
                note_type="Progress",
                progress_note="Fictional note: child followed the visual schedule.",
                staff_action_taken="Staff gave a short reminder before transition.",
                child_response="Responded positively.",
                follow_up_required=False,
                created_by_user_id=admin.id,
            )
        )


def seed() -> None:
    with SessionLocal() as db:
        roles = ensure_roles(db)
        admin = ensure_user(db, "demo_admin", "Demo Administrator", roles["Admin"])
        ensure_user(db, "demo_manager", "Demo Manager", roles["Manager"])
        ensure_user(db, "demo_warden", "Demo Warden", roles["Warden"])
        ensure_user(db, "demo_viewer", "Demo Viewer", roles["Viewer"])
        seed_organization(db)
        children = seed_children(db)
        db.flush()
        seed_accommodation(db, admin, children)
        seed_child_supporting_records(db, admin, children)
        seed_education(db, admin, children)
        seed_case_management(db, admin, children)
        seed_sponsorship_and_visits(db, admin, children)
        seed_development(db, admin, children)
        db.commit()
        print("CCMS demo data seed completed.")
        print("Demo users: demo_admin, demo_manager, demo_warden, demo_viewer")
        print(f"Demo password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
