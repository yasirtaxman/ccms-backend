import csv
from datetime import date, datetime
from io import BytesIO, StringIO
from openpyxl import load_workbook
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.child import Child
from app.services.excel_service import HEADERS, REQUIRED_HEADERS
from app.core.config import settings

def parse_upload(filename, content):
    if filename.lower().endswith(".csv"):
        rows=list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
    elif filename.lower().endswith(".xlsx"):
        ws=load_workbook(BytesIO(content),read_only=True,data_only=True).active; values=list(ws.values); headers=[str(v or "").strip() for v in values[0]]; rows=[dict(zip(headers,v)) for v in values[1:] if any(x is not None and str(x).strip() for x in v)]
    else: raise ValueError("Only .xlsx and .csv files are supported")
    if len(rows)>settings.IMPORT_MAX_ROWS: raise ValueError(f"Import exceeds maximum of {settings.IMPORT_MAX_ROWS} rows")
    return rows

def validate_rows(db: Session, rows):
    errors=[]; valid=[]; duplicate=set(); seen_child=set(); seen_file=set()
    child_ids={str(r.get("child_id") or "").strip() for r in rows}; file_nos={str(r.get("admission_file_no") or "").strip() for r in rows}
    existing_child=set(db.scalars(select(Child.child_id).where(Child.child_id.in_(child_ids))).all()) if child_ids else set()
    existing_file=set(db.scalars(select(Child.admission_file_no).where(Child.admission_file_no.in_(file_nos))).all()) if file_nos else set()
    for index,row in enumerate(rows,2):
        clean={h:(str(row.get(h)).strip() if row.get(h) is not None else "") for h in HEADERS}; before=len(errors)
        for h in REQUIRED_HEADERS:
            if not clean[h]: errors.append({"row":index,"field":h,"message":"Required field is missing"})
        for h in ("date_of_birth","admission_date"):
            try:
                raw_date = row.get(h)
                clean[h] = raw_date.date() if isinstance(raw_date, datetime) else raw_date if isinstance(raw_date, date) else datetime.strptime(clean[h], "%Y-%m-%d").date()
            except (ValueError,TypeError): errors.append({"row":index,"field":h,"message":"Date must use YYYY-MM-DD"})
        if clean["gender"] not in {"Male","Female","Other"}: errors.append({"row":index,"field":"gender","message":"Invalid gender"})
        if clean["status"] not in {"Active","Inactive","Discharged","Transferred"}: errors.append({"row":index,"field":"status","message":"Invalid status"})
        if clean["child_id"] in seen_child or clean["child_id"] in existing_child: errors.append({"row":index,"field":"child_id","message":"Duplicate child_id"}); duplicate.add(index)
        if clean["admission_file_no"] in seen_file or clean["admission_file_no"] in existing_file: errors.append({"row":index,"field":"admission_file_no","message":"Duplicate admission_file_no"}); duplicate.add(index)
        seen_child.add(clean["child_id"]); seen_file.add(clean["admission_file_no"])
        if len(errors)==before: valid.append(clean)
    return valid,errors,len(duplicate)
