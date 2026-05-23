import pandas as pd
import sys
import os
sys.path.append(
    os.path.join(os.path.dirname(__file__), "../ml")
)
from categorizer import categorize_batch

def run_pipeline(df, user_id, stmt_id):
    """
    Full analysis pipeline:
    1. Categorize all transactions
    2. Calculate statistics
    3. Return enriched DataFrame
    """

    print(f"Running pipeline for {len(df)} transactions...")
    print("  → Categorizing transactions...")
    descriptions = df["description"].tolist()
    categories   = categorize_batch(descriptions)

    df["category"]   = [c[0] for c in categories]
    df["confidence"] = [c[1] for c in categories]
    print(f"  Categorized {len(df)} transactions")
    total_debit  = round(float(df["debit"].sum()), 2)
    total_credit = round(float(df["credit"].sum()), 2)
    net_balance  = round(total_credit - total_debit, 2)
    debit_df     = df[df["type"] == "debit"]
    top_category = ""
    if not debit_df.empty:
        top_category = debit_df.groupby("category")["amount"]\
                                .sum().idxmax()
    category_summary = {}
    for cat in df["category"].unique():
        cat_df = df[df["category"] == cat]
        category_summary[cat] = {
            "total":       round(float(cat_df["amount"].sum()), 2),
            "count":       int(len(cat_df)),
            "percentage":  round(
                float(cat_df["amount"].sum()) /
                float(df["amount"].sum()) * 100
                if df["amount"].sum() > 0 else 0, 1
            )
        }
    savings_rate = (net_balance / total_credit * 100) \
                   if total_credit > 0 else 0
    if savings_rate >= 30:
        score, grade = 90, "A"
    elif savings_rate >= 20:
        score, grade = 75, "B"
    elif savings_rate >= 10:
        score, grade = 60, "C"
    elif savings_rate >= 0:
        score, grade = 45, "D"
    else:
        score, grade = 25, "F"

    stats = {
        "total_debit":      total_debit,
        "total_credit":     total_credit,
        "net_balance":      net_balance,
        "savings_rate":     round(savings_rate, 1),
        "top_category":     top_category,
        "category_summary": category_summary,
        "health_score":     score,
        "grade":            grade,
        "status":           "ready",
    }

    print(f"     Pipeline complete!")
    print(f"     Total Debit:  ₹{total_debit:,.2f}")
    print(f"     Total Credit: ₹{total_credit:,.2f}")
    print(f"     Health Score: {score}/100 ({grade})")

    return df, stats