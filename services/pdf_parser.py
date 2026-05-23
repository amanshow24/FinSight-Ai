import pdfplumber
import pandas as pd
import re
from datetime import datetime
COLUMNS = ["date", "description", "debit", "credit", "balance", "type"]
def detect_bank(text):
    text_lower = text.lower()
    if "state bank of india" in text_lower or "sbi" in text_lower:
        return "SBI"
    elif "hdfc bank" in text_lower or "hdfc" in text_lower:
        return "HDFC"
    elif "bank of india" in text_lower or " boi" in text_lower:
        return "BOI"
    elif "punjab national bank" in text_lower or "pnb" in text_lower:
        return "PNB"
    else:
        return "UNKNOWN"
def clean_amount(value):
    if not value or str(value).strip() in ["", "-", "N/A"]:
        return 0.0
    cleaned = re.sub(r"[₹,\s]", "", str(value))
    try:
        return float(cleaned)
    except:
        return 0.0
def clean_date(value):
    if not value:
        return None
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y",
        "%d/%m/%y", "%d-%b-%Y", "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(str(value).strip(), fmt).strftime("%Y-%m-%d")
        except:
            continue
    return str(value).strip()
def parse_sbi(tables):
    rows = []
    for table in tables:
        for row in table:
            if not row or len(row) < 5:
                continue
            try:
                date = clean_date(row[0])
                if not date or "date" in str(row[0]).lower():
                    continue
                desc  = str(row[1]).strip() if row[1] else ""
                debit  = clean_amount(row[2])
                credit = clean_amount(row[3])
                balance = clean_amount(row[4])
                txn_type = "credit" if credit > 0 else "debit"
                rows.append([date, desc, debit, credit, balance, txn_type])
            except:
                continue
    return rows
def parse_hdfc(tables):
    rows = []
    for table in tables:
        for row in table:
            if not row or len(row) < 6:
                continue
            try:
                date = clean_date(row[0])
                if not date or "date" in str(row[0]).lower():
                    continue
                desc    = str(row[1]).strip() if row[1] else ""
                debit   = clean_amount(row[4]) if len(row) > 4 else 0.0
                credit  = clean_amount(row[5]) if len(row) > 5 else 0.0
                balance = clean_amount(row[6]) if len(row) > 6 else 0.0
                txn_type = "credit" if credit > 0 else "debit"
                rows.append([date, desc, debit, credit, balance, txn_type])
            except:
                continue
    return rows
def parse_boi(tables):
    rows = []
    for table in tables:
        for row in table:
            if not row or len(row) < 5:
                continue
            try:
                date = clean_date(row[0])
                if not date or "date" in str(row[0]).lower():
                    continue
                desc    = str(row[1]).strip() if row[1] else ""
                debit   = clean_amount(row[2])
                credit  = clean_amount(row[3])
                balance = clean_amount(row[4])
                txn_type = "credit" if credit > 0 else "debit"
                rows.append([date, desc, debit, credit, balance, txn_type])
            except:
                continue
    return rows
def parse_pnb(tables):
    rows = []
    for table in tables:
        for row in table:
            if not row or len(row) < 5:
                continue
            try:
                date = clean_date(row[0])
                if not date or "date" in str(row[0]).lower():
                    continue
                desc    = str(row[1]).strip() if row[1] else ""
                debit   = clean_amount(row[2])
                credit  = clean_amount(row[3])
                balance = clean_amount(row[4])
                txn_type = "credit" if credit > 0 else "debit"
                rows.append([date, desc, debit, credit, balance, txn_type])
            except:
                continue
    return rows
def parse_generic(tables):
    rows = []
    for table in tables:
        for row in table:
            if not row or len(row) < 4:
                continue
            try:
                date = clean_date(row[0])
                if not date or "date" in str(row[0]).lower():
                    continue
                desc    = str(row[1]).strip() if row[1] else ""
                debit   = clean_amount(row[2]) if len(row) > 2 else 0.0
                credit  = clean_amount(row[3]) if len(row) > 3 else 0.0
                balance = clean_amount(row[4]) if len(row) > 4 else 0.0
                txn_type = "credit" if credit > 0 else "debit"
                rows.append([date, desc, debit, credit, balance, txn_type])
            except:
                continue
    return rows
def parse_bank_statement(file_path):
    """
    Main parser function.
    Input:  path to PDF file
    Output: clean pandas DataFrame
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            all_tables = []

            for page in pdf.pages:
                full_text += page.extract_text() or ""
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
        bank = detect_bank(full_text)
        print(f"Detected bank: {bank}")
        parsers = {
            "SBI":     parse_sbi,
            "HDFC":    parse_hdfc,
            "BOI":     parse_boi,
            "PNB":     parse_pnb,
            "UNKNOWN": parse_generic,
        }
        parser = parsers.get(bank, parse_generic)
        rows = parser(all_tables)

        if not rows:
            return None, "No transactions found in PDF"
        df = pd.DataFrame(rows, columns=COLUMNS)
        df = df[df["description"].str.strip() != ""]
        df = df[df["date"].notna()]
        df["amount"] = df.apply(
            lambda r: r["credit"] if r["credit"] > 0 else r["debit"], axis=1
        )
        df = df.sort_values("date").reset_index(drop=True)

        print(f"Parsed {len(df)} transactions from {bank} statement")
        return df, bank

    except Exception as e:
        print(f"Parser error: {str(e)}")
        return None, str(e)