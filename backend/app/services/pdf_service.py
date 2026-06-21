from datetime import datetime, timezone
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

def build_pdf_report(title, rows, username, filters):
    out=BytesIO(); doc=SimpleDocTemplate(out,pagesize=landscape(A4),rightMargin=24,leftMargin=24,topMargin=24,bottomMargin=28); styles=getSampleStyleSheet()
    story=[Paragraph("CCMS (Child Care Management System)",styles["Title"]),Paragraph(title,styles["Heading2"]),Paragraph(f"Generated {datetime.now(timezone.utc).isoformat()} by {username}",styles["Normal"]),Paragraph(f"Filters: {filters}",styles["Normal"]),Spacer(1,10)]
    columns=list(rows[0]) if rows else ["Result"]; data=[columns]+[[str(r.get(c,""))[:80] for c in columns] for r in rows] if rows else [["No data"]]
    table=Table(data,repeatRows=1); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1F4E78")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),6),("GRID",(0,0),(-1,-1),.25,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(table)
    def footer(canvas, _): canvas.drawRightString(landscape(A4)[0]-24,15,f"Page {canvas.getPageNumber()}")
    doc.build(story,onFirstPage=footer,onLaterPages=footer); out.seek(0); return out
