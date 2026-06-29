from datetime import UTC, datetime
import importlib.util
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from alembic.runtime.migration import MigrationContext
from app.core.config import settings
from app.core.database import engine
from app.core.deps import get_db, require_admin
from app.models.user import User
from app.utils.responses import success_response

router=APIRouter(tags=["System"])

@router.get("/health")
def health():
    return success_response("CCMS API is healthy",{"status":"healthy","service":settings.PROJECT_NAME,"environment":settings.ENVIRONMENT,"timestamp":datetime.now(UTC).isoformat()})

def system_checks(db: Session):
    checks={}
    try: db.execute(text("SELECT 1")); checks["database"]={"status":"ok"}
    except Exception: checks["database"]={"status":"error"}
    try:
        settings.upload_path.mkdir(parents=True,exist_ok=True)
        checks["upload_directory"]={"status":"ok","path":str(settings.upload_path)}
    except OSError: checks["upload_directory"]={"status":"error"}
    checks["excel_export"]={"status":"ok" if importlib.util.find_spec("openpyxl") else "error"}
    checks["pdf_export"]={"status":"ok" if importlib.util.find_spec("reportlab") else "error"}
    try:
        with engine.connect() as connection: revision=MigrationContext.configure(connection).get_current_revision()
        checks["alembic"]={"status":"ok","revision":revision}
    except Exception: checks["alembic"]={"status":"error"}
    return checks

def public_system_checks(checks: dict) -> dict:
    safe_checks = {}
    for name, value in checks.items():
        safe_value = {"status": value.get("status", "unknown")}
        if name == "alembic" and value.get("revision"):
            safe_value["revision"] = value["revision"]
        safe_checks[name] = safe_value
    return safe_checks

@router.get("/health/readiness")
def public_readiness(db: Session = Depends(get_db)):
    checks = system_checks(db)
    status = "ready" if all(v["status"] == "ok" for v in checks.values()) else "degraded"
    return success_response(
        "System readiness evaluated",
        {
            "status": status,
            "service": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
            "api_version": "1.0.0",
            "checks": public_system_checks(checks),
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

@router.get("/system/readiness")
def readiness(db:Session=Depends(get_db),_:User=Depends(require_admin)):
    checks=system_checks(db); status="ready" if all(v["status"]=="ok" for v in checks.values()) else "degraded"
    return success_response("System readiness evaluated",{"status":status,"checks":checks})

@router.get("/system/info")
def info(db:Session=Depends(get_db),_:User=Depends(require_admin)):
    database_connected=system_checks(db)["database"]["status"]=="ok"
    return success_response("System information",{"project_name":settings.PROJECT_NAME,"environment":settings.ENVIRONMENT,"api_version":"1.0.0","debug":settings.DEBUG,"database_connected":database_connected,"upload_dir":str(settings.upload_path),"features_enabled":{"rate_limiting":settings.RATE_LIMIT_ENABLED,"imports":True,"exports":True}})
