from io import BytesIO
from openpyxl import Workbook, load_workbook
from app.models.audit_log import AuditLog
from app.services.excel_service import HEADERS
from tests.test_dashboard_reports import auth


def upload(rows):
    wb=Workbook(); ws=wb.active; ws.append(HEADERS)
    for row in rows: ws.append(row)
    out=BytesIO(); wb.save(out); return ("children.xlsx",out.getvalue(),"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


VALID=["CH-101","ADM-101","Test Child","Father","Grandfather","Mother","Male","2015-01-01","Guardian","Uncle","00000-0000000-0","03000000000","Current","Permanent","Village","UC","Tehsil","District","Province","2026-01-01","Care","Active"]


def test_template_preview_commit_and_audit(client, db_session):
    _, headers=auth(db_session)
    template=client.get("/imports/templates/children.xlsx",headers=headers)
    assert template.status_code==200
    assert load_workbook(BytesIO(template.content)).sheetnames == ["Children Import","Instructions","Allowed Values"]
    preview=client.post("/imports/children/preview",headers=headers,files={"file":upload([VALID])})
    assert preview.status_code==200, preview.text
    assert preview.json()["valid_rows"]==1
    committed=client.post("/imports/children/commit",headers=headers,files={"file":upload([VALID])})
    assert committed.status_code==200, committed.text
    assert committed.json()["imported_count"]==1
    assert db_session.query(AuditLog).filter(AuditLog.action.in_(["IMPORT_PREVIEW","IMPORT_COMMIT"])).count()==2


def test_import_validation_duplicates_and_rbac(client, db_session):
    _, data_headers=auth(db_session,"operator","Data Entry Operator")
    duplicate=client.post("/imports/children/preview",headers=data_headers,files={"file":upload([VALID,VALID])})
    assert duplicate.status_code==200 and duplicate.json()["duplicate_rows"]==1
    assert client.post("/imports/children/commit",headers=data_headers,files={"file":upload([VALID])}).status_code==403
    _, viewer_headers=auth(db_session,"viewer2","Viewer")
    assert client.get("/imports/templates/children.xlsx",headers=viewer_headers).status_code==403


def test_exports_are_downloadable_and_audited(client, db_session):
    _, headers=auth(db_session)
    for path,content_type in (("/exports/children.xlsx","spreadsheetml"),("/exports/children.pdf","application/pdf")):
        response=client.get(path,headers=headers)
        assert response.status_code==200
        assert content_type in response.headers["content-type"]
    assert db_session.query(AuditLog).filter(AuditLog.action.in_(["EXPORT_EXCEL","EXPORT_PDF"])).count()==2
