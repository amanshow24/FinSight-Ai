import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

sys.path.append(
    os.path.join(os.path.dirname(__file__), "../ml")
)
from categorizer import categorize_batch
from anomaly_detector import detect_batch

def run_pipeline(df, user_id, stmt_id):
    print(f"🔄 Running pipeline for {len(df)} transactions...")

    # ── Categorize ────────────────────────────
    print("  → Categorizing transactions...")
    descriptions = df["description"].tolist()
    categories   = categorize_batch(descriptions)
    df["category"]    = [c[0] for c in categories]
    df["confidence"]  = [c[1] for c in categories]
    print(f"  ✅ Categorized {len(df)} transactions")

    # ── Anomaly Detection ─────────────────────
    print("  → Detecting anomalies...")
    df["parsed_date"] = pd.to_datetime(
        df["date"], errors="coerce"
    )
    df["hour"] = df["parsed_date"].dt.hour.fillna(12).astype(int)
    df["day_of_week"] = df["parsed_date"].dt.dayofweek.fillna(0).astype(int)

    txn_list = [
        {
            "amount":      float(row["amount"]),
            "hour":        int(row["hour"]),
            "day_of_week": int(row["day_of_week"])
        }
        for _, row in df.iterrows()
    ]

    anomaly_results    = detect_batch(txn_list)
    df["is_anomaly"]   = [r["is_anomaly"]  for r in anomaly_results]
    df["anomaly_score"]= [r["score"]       for r in anomaly_results]
    df["anomaly_reason"]=[r["reason"]      for r in anomaly_results]

    anomaly_count = int(df["is_anomaly"].sum())
    print(f"  ✅ Found {anomaly_count} anomalies")

    # ── Statistics ────────────────────────────
    total_debit  = round(float(df["debit"].sum()), 2)
    total_credit = round(float(df["credit"].sum()), 2)
    net_balance  = round(total_credit - total_debit, 2)

    debit_df     = df[df["type"] == "debit"]
    top_category = ""
    if not debit_df.empty:
        top_category = debit_df.groupby("category")["amount"]\
                                .sum().idxmax()

    # Category summary
    category_summary = {}
    for cat in df["category"].unique():
        cat_df = df[df["category"] == cat]
        category_summary[cat] = {
            "total":      round(float(cat_df["amount"].sum()), 2),
            "count":      int(len(cat_df)),
            "percentage": round(
                float(cat_df["amount"].sum()) /
                float(df["amount"].sum()) * 100
                if df["amount"].sum() > 0 else 0, 1
            )
        }

    # Health score
    savings_rate = (
        net_balance / total_credit * 100
    ) if total_credit > 0 else 0

    anomaly_penalty = min(anomaly_count * 5, 20)

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

    score = max(0, score - anomaly_penalty)

    stats = {
        "total_debit":      total_debit,
        "total_credit":     total_credit,
        "net_balance":      net_balance,
        "savings_rate":     round(savings_rate, 1),
        "top_category":     top_category,
        "category_summary": category_summary,
        "health_score":     score,
        "grade":            grade,
        "anomaly_count":    anomaly_count,
        "status":           "ready",
    }

    print(f"  ✅ Pipeline complete!")
    print(f"     Debit:   ₹{total_debit:,.2f}")
    print(f"     Credit:  ₹{total_credit:,.2f}")
    print(f"     Score:   {score}/100 ({grade})")
    print(f"     Anomalies: {anomaly_count}")

    return df, stats