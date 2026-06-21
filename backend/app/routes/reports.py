from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import csv
import io
from datetime import datetime, timedelta
import uuid

from app.auth import require_roles, UserSession
from app.db import get_db

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# Directory to save generated reports
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class ReportRequest(BaseModel):
    organizationId: str
    reportType: str  # PDF, Excel, CSV
    periodType: str  # Daily, Weekly, Monthly


class ReportResponse(BaseModel):
    reportId: str
    organizationId: str
    reportType: str
    periodType: str
    filePath: str
    generatedAt: str


# ------------------------------------------------------------------ #
#  Helper: collect report data                                         #
# ------------------------------------------------------------------ #
def _collect_report_data(db, organizationId: str, periodType: str):
    """Return org, sites, meters and per-meter stats."""
    org = db["organizations"].find_one({"organizationId": organizationId})
    if not org:
        return None, None, None, None

    # Period window
    period_days = {"Daily": 1, "Weekly": 7, "Monthly": 30}.get(periodType, 7)
    since = (datetime.utcnow() - timedelta(days=period_days)).isoformat() + "Z"

    sites = list(db["sites"].find({"organizationId": organizationId}))
    site_ids = [s["siteId"] for s in sites]
    meters = list(db["meters"].find({"siteId": {"$in": site_ids}}))

    rows = []
    for meter in meters:
        site = next((s for s in sites if s["siteId"] == meter["siteId"]), {"name": "Unknown"})
        latest = db["readings"].find_one({"meterId": meter["meterId"]}, sort=[("timestamp", -1)])
        earliest = db["readings"].find_one(
            {"meterId": meter["meterId"], "timestamp": {"$gte": since}},
            sort=[("timestamp", 1)]
        )
        load = round(latest["powerKw"], 2) if latest else 0.0
        energy = round(max(0.0, latest["energyKwh"] - earliest["energyKwh"]), 2) if (latest and earliest) else 0.0
        rows.append({
            "site": site["name"],
            "serial": meter["serialNumber"],
            "label": meter["label"],
            "status": meter["status"],
            "load_kw": load,
            "energy_kwh": energy,
        })

    return org, sites, rows, since


# ------------------------------------------------------------------ #
#  CSV generator                                                       #
# ------------------------------------------------------------------ #
def _generate_csv(file_path: str, report_id: str, org, periodType: str, rows, generated_at: str):
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Smart Energy System Report"])
        w.writerow(["Report ID", report_id])
        w.writerow(["Organization", org["name"]])
        w.writerow(["Period", periodType])
        w.writerow(["Generated At", generated_at])
        w.writerow([])
        w.writerow(["SITE NAME", "METER SERIAL", "METER LABEL", "STATUS",
                    "CURRENT LOAD (kW)", "ENERGY CONSUMED (kWh)"])
        for r in rows:
            w.writerow([r["site"], r["serial"], r["label"], r["status"], r["load_kw"], r["energy_kwh"]])
        w.writerow([])
        w.writerow(["TOTALS", "", "", "",
                    round(sum(r["load_kw"] for r in rows), 2),
                    round(sum(r["energy_kwh"] for r in rows), 2)])


# ------------------------------------------------------------------ #
#  Excel generator                                                     #
# ------------------------------------------------------------------ #
def _generate_excel(file_path: str, report_id: str, org, periodType: str, rows, generated_at: str):
    from openpyxl import Workbook
    from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                                  GradientFill)
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = f"{periodType} Energy Report"

    # ---- colour palette ----
    DARK_BG   = "0D1117"
    MID_BG    = "161B22"
    ACCENT    = "06B6D4"   # cyan
    GREEN     = "22C55E"
    AMBER     = "F59E0B"
    RED_CLR   = "EF4444"
    WHITE     = "FFFFFF"
    LIGHT_GRY = "E2E8F0"
    SUBTEXT   = "94A3B8"

    def make_fill(hex_color):
        return PatternFill("solid", fgColor=hex_color)

    def thin_border():
        s = Side(style="thin", color="30363D")
        return Border(left=s, right=s, top=s, bottom=s)

    # ---- Title section ----
    ws.merge_cells("A1:F1")
    title_cell = ws["A1"]
    title_cell.value = "Smart Energy Monitoring System"
    title_cell.font = Font(name="Calibri", bold=True, size=18, color=ACCENT)
    title_cell.fill = make_fill(DARK_BG)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    ws.merge_cells("A2:F2")
    sub_cell = ws["A2"]
    sub_cell.value = f"{periodType} Energy Report  |  {org['name']}"
    sub_cell.font = Font(name="Calibri", size=11, color=SUBTEXT)
    sub_cell.fill = make_fill(DARK_BG)
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    # ---- Meta block ----
    meta = [
        ("Report ID", report_id),
        ("Organization", org["name"]),
        ("Period", periodType),
        ("Generated At", generated_at),
    ]
    for i, (k, v) in enumerate(meta, start=3):
        ws.row_dimensions[i].height = 18
        kc = ws.cell(row=i, column=1, value=k)
        kc.font = Font(name="Calibri", bold=True, color=SUBTEXT, size=10)
        kc.fill = make_fill(MID_BG)
        kc.alignment = Alignment(horizontal="left", vertical="center", indent=1)

        vc = ws.cell(row=i, column=2, value=v)
        vc.font = Font(name="Calibri", color=WHITE, size=10)
        vc.fill = make_fill(MID_BG)
        vc.alignment = Alignment(horizontal="left", vertical="center")
        for col in range(3, 7):
            ec = ws.cell(row=i, column=col, value="")
            ec.fill = make_fill(MID_BG)

    ws.row_dimensions[7].height = 8  # spacer

    # ---- Header row ----
    HEADERS = ["Site Name", "Meter Serial", "Meter Label", "Status",
               "Current Load (kW)", "Energy Consumed (kWh)"]
    HDR_ROW = 8
    ws.row_dimensions[HDR_ROW].height = 24
    for col_idx, hdr in enumerate(HEADERS, start=1):
        c = ws.cell(row=HDR_ROW, column=col_idx, value=hdr)
        c.font = Font(name="Calibri", bold=True, color=WHITE, size=10)
        c.fill = PatternFill("solid", fgColor="1E293B")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border()

    # ---- Data rows ----
    for row_offset, r in enumerate(rows):
        excel_row = HDR_ROW + 1 + row_offset
        ws.row_dimensions[excel_row].height = 20
        bg = "0D1117" if row_offset % 2 == 0 else "111827"

        status_color = {"Active": GREEN, "Faulty": RED_CLR, "Inactive": AMBER}.get(r["status"], SUBTEXT)

        values = [r["site"], r["serial"], r["label"], r["status"], r["load_kw"], r["energy_kwh"]]
        for col_idx, val in enumerate(values, start=1):
            c = ws.cell(row=excel_row, column=col_idx, value=val)
            c.fill = make_fill(bg)
            c.border = thin_border()
            c.alignment = Alignment(horizontal="center", vertical="center")

            if col_idx == 4:  # Status
                c.font = Font(name="Calibri", size=10, color=status_color, bold=True)
            elif col_idx in (5, 6):
                c.font = Font(name="Calibri", size=10, color=ACCENT)
                c.number_format = "#,##0.00"
            else:
                c.font = Font(name="Calibri", size=10, color=WHITE)

    # ---- Totals row ----
    total_row = HDR_ROW + 1 + len(rows)
    ws.row_dimensions[total_row].height = 24
    total_vals = ["TOTALS", "", "", "",
                  round(sum(r["load_kw"] for r in rows), 2),
                  round(sum(r["energy_kwh"] for r in rows), 2)]
    for col_idx, val in enumerate(total_vals, start=1):
        c = ws.cell(row=total_row, column=col_idx, value=val)
        c.fill = PatternFill("solid", fgColor="1E3A5F")
        c.font = Font(name="Calibri", bold=True, color=ACCENT, size=10)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border()
        if col_idx in (5, 6):
            c.number_format = "#,##0.00"

    # ---- Column widths ----
    col_widths = [22, 24, 28, 12, 20, 22]
    for i, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width

    # ---- Freeze panes ----
    ws.freeze_panes = f"A{HDR_ROW + 1}"

    # Tab colour
    ws.sheet_properties.tabColor = ACCENT

    wb.save(file_path)


# ------------------------------------------------------------------ #
#  PDF generator                                                       #
# ------------------------------------------------------------------ #
def _generate_pdf(file_path: str, report_id: str, org, periodType: str, rows, generated_at: str):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    # ---- colour palette ----
    DARK     = colors.HexColor("#0D1117")
    MID      = colors.HexColor("#161B22")
    ACCENT   = colors.HexColor("#06B6D4")
    GREEN    = colors.HexColor("#22C55E")
    AMBER    = colors.HexColor("#F59E0B")
    RED      = colors.HexColor("#EF4444")
    WHITE    = colors.white
    SUBTEXT  = colors.HexColor("#94A3B8")
    ROWALT   = colors.HexColor("#111827")
    ROWMAIN  = colors.HexColor("#0D1117")
    HDRBG    = colors.HexColor("#1E293B")
    TOTALBG  = colors.HexColor("#1E3A5F")

    page_w, page_h = landscape(A4)
    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(A4),
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title", fontSize=22, textColor=ACCENT,
        fontName="Helvetica-Bold", alignment=TA_LEFT, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "subtitle", fontSize=11, textColor=SUBTEXT,
        fontName="Helvetica", alignment=TA_LEFT, spaceAfter=0
    )
    meta_label_style = ParagraphStyle(
        "meta_label", fontSize=9, textColor=SUBTEXT,
        fontName="Helvetica-Bold", alignment=TA_LEFT
    )
    meta_val_style = ParagraphStyle(
        "meta_val", fontSize=9, textColor=WHITE,
        fontName="Helvetica", alignment=TA_LEFT
    )

    story = []

    # ---- Header banner ----
    banner_data = [[
        Paragraph("Smart Energy Monitoring System", title_style),
        Paragraph(f"{periodType} Energy Report", subtitle_style)
    ]]
    banner = Table(banner_data, colWidths=[page_w * 0.55, page_w * 0.35])
    banner.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), DARK),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(banner)
    story.append(Spacer(1, 4*mm))

    # ---- Meta block (2-col) ----
    meta_left = [
        [Paragraph("Report ID", meta_label_style), Paragraph(report_id, meta_val_style)],
        [Paragraph("Organization", meta_label_style), Paragraph(org["name"], meta_val_style)],
    ]
    meta_right = [
        [Paragraph("Period", meta_label_style), Paragraph(periodType, meta_val_style)],
        [Paragraph("Generated At", meta_label_style), Paragraph(generated_at[:19].replace("T", " "), meta_val_style)],
    ]
    meta_tbl_l = Table(meta_left, colWidths=[35*mm, 80*mm])
    meta_tbl_r = Table(meta_right, colWidths=[35*mm, 80*mm])
    for mt in (meta_tbl_l, meta_tbl_r):
        mt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), MID),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ]))

    meta_outer = Table([[meta_tbl_l, Spacer(8*mm, 1), meta_tbl_r]])
    meta_outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(meta_outer)
    story.append(Spacer(1, 6*mm))

    # ---- Data table ----
    hdr_style = ParagraphStyle("hdr", fontSize=9, textColor=WHITE,
                               fontName="Helvetica-Bold", alignment=TA_CENTER)
    cell_style = ParagraphStyle("cell", fontSize=9, textColor=WHITE,
                                fontName="Helvetica", alignment=TA_CENTER)
    num_style  = ParagraphStyle("num", fontSize=9, textColor=ACCENT,
                                fontName="Helvetica", alignment=TA_RIGHT)

    def status_para(s):
        colour = {
            "Active":   "#22C55E",
            "Faulty":   "#EF4444",
            "Inactive": "#F59E0B"
        }.get(s, "#94A3B8")
        return Paragraph(
            f'<font color="{colour}"><b>{s}</b></font>',
            ParagraphStyle("st", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER)
        )

    table_data = [[
        Paragraph("Site Name",              hdr_style),
        Paragraph("Meter Serial",           hdr_style),
        Paragraph("Meter Label",            hdr_style),
        Paragraph("Status",                 hdr_style),
        Paragraph("Current Load (kW)",      hdr_style),
        Paragraph("Energy Consumed (kWh)",  hdr_style),
    ]]

    for r in rows:
        table_data.append([
            Paragraph(r["site"],   cell_style),
            Paragraph(r["serial"], cell_style),
            Paragraph(r["label"],  cell_style),
            status_para(r["status"]),
            Paragraph(f'{r["load_kw"]:.2f}',   num_style),
            Paragraph(f'{r["energy_kwh"]:.2f}', num_style),
        ])

    # Totals row
    total_style = ParagraphStyle("tot", fontSize=9, textColor=ACCENT,
                                 fontName="Helvetica-Bold", alignment=TA_CENTER)
    tot_num = ParagraphStyle("totnum", fontSize=9, textColor=ACCENT,
                             fontName="Helvetica-Bold", alignment=TA_RIGHT)
    table_data.append([
        Paragraph("TOTALS", total_style),
        Paragraph("", total_style),
        Paragraph("", total_style),
        Paragraph("", total_style),
        Paragraph(f'{sum(r["load_kw"] for r in rows):.2f}',    tot_num),
        Paragraph(f'{sum(r["energy_kwh"] for r in rows):.2f}', tot_num),
    ])

    # Col widths that add up to usable page width
    usable_w = page_w - 30*mm
    col_widths = [
        usable_w * 0.18,
        usable_w * 0.17,
        usable_w * 0.22,
        usable_w * 0.10,
        usable_w * 0.16,
        usable_w * 0.17,
    ]

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    ts = TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0), HDRBG),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        # Alternating rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [ROWMAIN, ROWALT]),
        ("TOPPADDING",    (0, 1), (-1, -2), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 5),
        # Totals row
        ("BACKGROUND",    (0, -1), (-1, -1), TOTALBG),
        ("TOPPADDING",    (0, -1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        # Grid
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#30363D")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ])
    tbl.setStyle(ts)
    story.append(tbl)

    story.append(Spacer(1, 6*mm))

    # ---- Footer ----
    footer_style = ParagraphStyle(
        "footer", fontSize=8, textColor=SUBTEXT,
        fontName="Helvetica", alignment=TA_CENTER
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=SUBTEXT))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"Generated by Apex Energy Smart Monitoring System  •  {generated_at[:10]}  •  Confidential",
        footer_style
    ))

    # ---- Background canvas callback ----
    def _on_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK)
        canvas.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)


# ------------------------------------------------------------------ #
#  Endpoint: generate                                                  #
# ------------------------------------------------------------------ #
@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    request: ReportRequest,
    current_user: UserSession = Depends(require_roles(["Admin", "Manager"]))
):
    db = get_db()

    org, sites, rows, since = _collect_report_data(db, request.organizationId, request.periodType)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{request.organizationId}' not found."
        )

    if rows is None:
        rows = []

    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    generated_at = datetime.utcnow().isoformat() + "Z"

    # Determine extension and media type
    ext_map   = {"CSV": "csv", "Excel": "xlsx", "PDF": "pdf"}
    media_map = {
        "CSV":   "text/csv",
        "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "PDF":   "application/pdf",
    }
    ext        = ext_map.get(request.reportType, "csv")
    media_type = media_map.get(request.reportType, "text/csv")

    filename  = f"energy_report_{request.periodType.lower()}_{report_id[:8]}.{ext}"
    file_path = os.path.join(REPORTS_DIR, filename)

    try:
        if request.reportType == "PDF":
            _generate_pdf(file_path, report_id, org, request.periodType, rows, generated_at)
        elif request.reportType == "Excel":
            _generate_excel(file_path, report_id, org, request.periodType, rows, generated_at)
        else:
            _generate_csv(file_path, report_id, org, request.periodType, rows, generated_at)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate {request.reportType} report: {str(e)}"
        )

    # Save report metadata (store media_type for download endpoint)
    report_doc = {
        "reportId":        report_id,
        "organizationId":  request.organizationId,
        "requestedByUserId": current_user.userId,
        "reportType":      request.reportType,
        "periodType":      request.periodType,
        "filePath":        file_path,
        "mediaType":       media_type,
        "generatedAt":     generated_at,
    }
    db["reports"].insert_one(report_doc)

    return ReportResponse(
        reportId=report_id,
        organizationId=request.organizationId,
        reportType=request.reportType,
        periodType=request.periodType,
        filePath=f"/api/reports/{report_id}/download",
        generatedAt=generated_at,
    )


# ------------------------------------------------------------------ #
#  Endpoint: download                                                  #
# ------------------------------------------------------------------ #
@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    current_user: UserSession = Depends(require_roles(["Admin", "Manager"]))
):
    db = get_db()
    report = db["reports"].find_one({"reportId": report_id})
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found."
        )

    file_path = report["filePath"]
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The report file could not be found on disk."
        )

    media_type = report.get("mediaType", "text/csv")
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type=media_type,
    )
