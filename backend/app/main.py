from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import SecurityHeadersMiddleware

from app.api.v1.children import router as children_router
from app.api.v1.documents import router as documents_router
from app.api.v1.auth import router as auth_router
from app.api.v1.roles import router as roles_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.sponsors import router as sponsors_router
from app.api.v1.accommodation import router as accommodation_router
from app.api.v1.medical import router as medical_router
from app.api.v1.education import router as education_router
from app.api.v1.case_management import router as case_management_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.consolidated_reports import router as reports_router
from app.api.v1.exports import router as exports_router
from app.api.v1.imports import router as imports_router
from app.api.v1.users import router as users_router
from app.api.v1.system import router as system_router
from app.api.v1.child_attendance import router as child_attendance_router
from app.api.v1.visitors import router as visitors_router
from app.api.v1.organization_profile import router as organization_profile_router
from app.api.v1.development import router as development_router

TAGS_METADATA = [{"name": name} for name in ["Authentication","Users","Roles","Children","Documents","Sponsors","Accommodation","Medical","Education","Case Management","Child Development Profile","Dashboards and Search","Consolidated Reports","Exports","Imports","System","Audit Logs","Organization Profile"]]

configure_logging()

app = FastAPI(
    title="CCMS API",
    description="Child Care Management System Backend API",
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(CORSMiddleware, allow_origins=settings.BACKEND_CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)

app.include_router(children_router)
app.include_router(documents_router)
app.include_router(auth_router)
app.include_router(roles_router)
app.include_router(audit_logs_router)
app.include_router(sponsors_router)
app.include_router(accommodation_router)
app.include_router(medical_router)
app.include_router(education_router)
app.include_router(case_management_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(exports_router)
app.include_router(imports_router)
app.include_router(users_router)
app.include_router(system_router)
app.include_router(child_attendance_router)
app.include_router(visitors_router)
app.include_router(organization_profile_router)
app.include_router(development_router)


@app.get("/")
def root():
    return {
        "message": "CCMS API Running"
    }
