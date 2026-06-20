from fastapi import FastAPI

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

app = FastAPI(
    title="CCMS - Child Care Management System",
    version="1.0.0"
)

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


@app.get("/")
def root():
    return {
        "message": "CCMS API Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
