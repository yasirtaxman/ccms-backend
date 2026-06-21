from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.deps import can_create_or_update, get_db, require_manager
from app.models.child import Child
from app.models.user import User
from app.schemas.import_export import ImportCommitResponse, ImportPreviewResponse
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.services.excel_service import build_child_import_template
from app.services.import_service import parse_upload, validate_rows
from app.utils.files import enforce_upload_size, sanitize_filename

router=APIRouter(prefix="/imports",tags=["Imports"])
async def load(file):
    enforce_upload_size(file)
    try: return parse_upload(sanitize_filename(file.filename),await file.read())
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.get("/templates/children.xlsx")
def template(_:User=Depends(can_create_or_update)): return StreamingResponse(build_child_import_template(),media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":'attachment; filename="ccms-children-import-template.xlsx"'})
@router.post("/children/preview",response_model=ImportPreviewResponse)
async def preview(file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(can_create_or_update)):
    rows=await load(file); valid,errors,duplicates=validate_rows(db,rows); add_audit_log(db,user_id=user.id,action=AuditAction.IMPORT_PREVIEW,module=AuditModule.IMPORT_EXPORT,new_values={"filename":file.filename,"total_rows":len(rows),"valid_rows":len(valid)}); db.commit()
    return ImportPreviewResponse(total_rows=len(rows),valid_rows=len(valid),invalid_rows=len(rows)-len(valid),duplicate_rows=duplicates,validation_errors=errors,preview_data=valid[:100])
@router.post("/children/commit",response_model=ImportCommitResponse)
async def commit(file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(require_manager)):
    rows=await load(file); valid,errors,_=validate_rows(db,rows)
    if errors: db.rollback(); raise HTTPException(422,{"message":"Import validation failed","errors":errors})
    created=[]
    try:
        objects=[Child(**row) for row in valid]; db.add_all(objects); db.flush(); created=[o.id for o in objects]
        add_audit_log(db,user_id=user.id,action=AuditAction.IMPORT_COMMIT,module=AuditModule.IMPORT_EXPORT,new_values={"imported_count":len(objects),"uploaded_filename":file.filename,"user_id":user.id,"created_child_ids":created}); db.commit()
    except Exception: db.rollback(); raise
    return ImportCommitResponse(imported_count=len(created),skipped_count=0,errors=[],created_child_ids=created)
