from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.deps import can_operational_read, get_db
from app.models.user import User
from app.services import report_service
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.services.excel_service import build_excel_report,build_full_profile_excel
from app.services.pdf_service import build_pdf_report,build_full_profile_pdf
from app.services.profile_export_service import build_full_child_profile
from app.core.config import settings

router=APIRouter(prefix="/exports",tags=["Exports"])
REPORTS={"children":report_service.children_report,"sponsors":report_service.sponsors_report,"sponsorships":report_service.sponsorships_report,"accommodation":report_service.accommodation_report,"medical":report_service.medical_report,"education":report_service.education_report,"case-management":report_service.case_report}
def export(db,user,name,kind):
    report=REPORTS[name](db,user.username,limit=settings.EXPORT_MAX_ROWS,offset=0); rows=report.data
    stream=build_excel_report(name.replace("-"," ").title(),rows,user.username,report.filters_applied) if kind=="xlsx" else build_pdf_report(name.replace("-"," ").title(),rows,user.username,report.filters_applied)
    add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_EXCEL if kind=="xlsx" else AuditAction.EXPORT_PDF,module=AuditModule.IMPORT_EXPORT,new_values={"report_type":name,"filters":report.filters_applied}); db.commit()
    media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if kind=="xlsx" else "application/pdf"
    return StreamingResponse(stream,media_type=media,headers={"Content-Disposition":f'attachment; filename="ccms-{name}.{kind}"'})
for name in REPORTS:
    def make(n,k):
        def endpoint(db:Session=Depends(get_db),user:User=Depends(can_operational_read)): return export(db,user,n,k)
        return endpoint
    router.add_api_route(f"/{name}.xlsx",make(name,"xlsx"),methods=["GET"])
    if name != "sponsorships": router.add_api_route(f"/{name}.pdf",make(name,"pdf"),methods=["GET"])

def profile_export(child_id,kind,db,user):
    profile=build_full_child_profile(db,child_id,{role.name for role in user.roles})
    stream=build_full_profile_excel(profile,user.username) if kind=="xlsx" else build_full_profile_pdf(profile,user.username)
    add_audit_log(db,user_id=user.id,action=AuditAction.EXPORT_EXCEL if kind=="xlsx" else AuditAction.EXPORT_PDF,module=AuditModule.IMPORT_EXPORT,record_id=child_id,new_values={"report_type":"full-child-profile"}); db.commit()
    media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if kind=="xlsx" else "application/pdf"; return StreamingResponse(stream,media_type=media,headers={"Content-Disposition":f'attachment; filename="ccms-child-{child_id}.{kind}"'})
@router.get("/full-child-profile/{child_id}.xlsx")
def profile_xlsx(child_id:int,db:Session=Depends(get_db),user:User=Depends(can_operational_read)): return profile_export(child_id,"xlsx",db,user)
@router.get("/full-child-profile/{child_id}.pdf")
def profile_pdf(child_id:int,db:Session=Depends(get_db),user:User=Depends(can_operational_read)): return profile_export(child_id,"pdf",db,user)
