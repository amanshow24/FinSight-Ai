from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

doc = SimpleDocTemplate("test_statement.pdf", pagesize=A4)

data = [
    ["Date", "Description", "Debit", "Credit", "Balance"],
    ["01/01/2026", "Opening Balance", "", "", "50000.00"],
    ["02/01/2026", "UPI/ZOMATO/ORDER123", "350.00", "", "49650.00"],
    ["03/01/2026", "SALARY CREDIT", "", "45000.00", "94650.00"],
    ["04/01/2026", "ATM WITHDRAWAL", "2000.00", "", "92650.00"],
    ["05/01/2026", "UPI/SWIGGY/ORDER456", "280.00", "", "92370.00"],
    ["06/01/2026", "NETFLIX SUBSCRIPTION", "649.00", "", "91721.00"],
    ["07/01/2026", "UPI/AMAZON/ORDER789", "1299.00", "", "90422.00"],
    ["08/01/2026", "ELECTRICITY BILL", "1200.00", "", "89222.00"],
    ["09/01/2026", "UPI/UBER/RIDE123", "180.00", "", "89042.00"],
    ["10/01/2026", "FREELANCE PAYMENT", "", "15000.00", "104042.00"],
]

table = Table(data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.grey),
    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
    ('GRID',       (0,0), (-1,-1), 0.5, colors.black),
    ('FONTSIZE',   (0,0), (-1,-1), 9),
]))

doc.build([table])
print("test_statement.pdf created!")