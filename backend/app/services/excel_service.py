from datetime import datetime, timezone
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADERS = ["child_id","admission_file_no","full_name","father_name","grandfather_name","mother_name","gender","date_of_birth","guardian_name","guardian_relationship","guardian_cnic","guardian_mobile","current_address","permanent_address","village_mohallah","union_council","tehsil","district","province","admission_date","reason_for_admission","status"]

def _finish(ws, header_row, columns):
    fill=PatternFill("solid", fgColor="1F4E78")
    for c in ws[header_row]: c.font=Font(color="FFFFFF",bold=True); c.fill=fill; c.alignment=Alignment(horizontal="center")
    ws.freeze_panes=f"A{header_row+1}"; ws.auto_filter.ref=f"A{header_row}:{get_column_letter(len(columns))}{ws.max_row}"
    for i,name in enumerate(columns,1):
        width=max([len(str(name))]+[len(str(ws.cell(r,i).value or "")) for r in range(header_row+1,ws.max_row+1)])
        ws.column_dimensions[get_column_letter(i)].width=min(width+2,45)

def build_excel_report(title, rows, username, filters):
    wb=Workbook(); ws=wb.active; ws.title="Report"
    ws.append(["CCMS (Child Care Management System)"]); ws.append([title]); ws.append([f"Generated: {datetime.now(timezone.utc).isoformat()} by {username}"]); ws.append([f"Filters: {filters}"])
    columns=list(rows[0]) if rows else ["No data"]
    ws.append(columns)
    for row in rows: ws.append([row.get(c) for c in columns])
    _finish(ws,5,columns); out=BytesIO(); wb.save(out); out.seek(0); return out

def build_child_import_template():
    wb=Workbook(); ws=wb.active; ws.title="Children Import"
    ws.append(HEADERS); ws.append(["CH-0001","ADM-0001","Sample Child","Father","Grandfather","Mother","Male","2015-01-31","Guardian","Uncle","00000-0000000-0","03000000000","Current address","Permanent address","Village","UC","Tehsil","District","Province","2026-01-01","Care required","Active"]); _finish(ws,1,HEADERS)
    ins=wb.create_sheet("Instructions"); ins.append(["All columns are required. Dates must use YYYY-MM-DD. Maximum 5000 rows. Remove the sample row before upload."])
    allowed=wb.create_sheet("Allowed Values"); allowed.append(["Field","Allowed values"]); allowed.append(["gender","Male, Female, Other"]); allowed.append(["status","Active, Inactive, Discharged, Transferred"])
    out=BytesIO(); wb.save(out); out.seek(0); return out
