from app.core.database import engine, Base

from app.models.child import Child
from app.models.document import Document

from app.models.user import User
from app.models.role import Role, UserRole
from app.models.audit_log import AuditLog
from app.models.sponsor import Sponsor, ChildSponsorship
from app.models.accommodation import Building, Block, Floor, Room, Bed, BedAllocation
from app.models.medical_profile import MedicalProfile
from app.models.medical_visit import MedicalVisit
from app.models.medication import Medication
from app.models.vaccination import Vaccination
from app.models.medical_document import MedicalDocument
from app.models.school import School
from app.models.education_record import EducationRecord
from app.models.exam_result import ExamResult
from app.models.attendance import Attendance
from app.models.education_document import EducationDocument
from app.models.case_management import (
    ChildCaseProfile, CaseNote, CounselingSession, IncidentRecord, CarePlan, CaseReview
)

Base.metadata.create_all(bind=engine)

print("Tables created successfully.")
