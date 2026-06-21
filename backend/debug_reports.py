import sys, os, traceback
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db import get_db
from app.routes.reports import _collect_report_data, _generate_pdf, _generate_excel, _generate_csv
from datetime import datetime

db = get_db()
org, sites, rows, since = _collect_report_data(db, "org_apex", "Weekly")
print(f"Org: {org['name']}, Rows: {len(rows)}")

generated_at = datetime.utcnow().isoformat() + "Z"
rid = "rpt_test123"

# Test CSV
csv_path = "static/reports/test_output.csv"
_generate_csv(csv_path, rid, org, "Weekly", rows, generated_at)
print(f"CSV OK: {os.path.getsize(csv_path)} bytes")

# Test Excel
xlsx_path = "static/reports/test_output.xlsx"
_generate_excel(xlsx_path, rid, org, "Weekly", rows, generated_at)
print(f"Excel OK: {os.path.getsize(xlsx_path)} bytes")

# Test PDF
pdf_path = "static/reports/test_output.pdf"
_generate_pdf(pdf_path, rid, org, "Weekly", rows, generated_at)
print(f"PDF OK: {os.path.getsize(pdf_path)} bytes")

print("\nAll formats generated successfully!")
