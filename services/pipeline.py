import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
sys.path.append(
    os.path.join(os.path.dirname(__file__), "../ml")
)

from categorizer      import categorize_batch
from anomaly_detector import detect_batch
from predictor        import predict_all_categories
from health_scorer    import calculate_health_score


def run_pipeline(df, user_id, stmt_id):
    """
    Complete 4-stage analysis pipeline:
    Stage 1 → Categorize transactions
    Stage 2 → Detect anomalies
    Stage 3 → Predict next 30 days
    Stage 4 → Calculate health score
    """
    print(f"\n Pipeline starting — {len(df)} transactions")
    print("\n  Stage 1: Categorizing...")
    descriptions = df["description"].tolist()
    categories   = categorize_batch(descriptions)

    df["category"]    = [c[0] for c in categories]
    df["confidence"]  = [c[1] for c in categories]
    print(f"   {len(df)} transactions categorized")
    print("\n   Stage 2: Detecting anomalies...")
    df["parsed_date"] = pd.to_datetime(
        df["date"], errors="coerce"
    )
    df["hour"] = df["parsed_date"]\
                   .dt.hour.fillna(12).astype(int)
    df["day_of_week"] = df["parsed_date"]\
                          .dt.dayofweek.fillna(0).astype(int)

    txn_list = [
        {
            "amount":      float(row["amount"]),
            "hour":        int(row["hour"]),
            "day_of_week": int(row["day_of_week"])
        }
        for _, row in df.iterrows()
    ]

    anomaly_results     = detect_batch(txn_list)
    df["is_anomaly"]    = [r["is_anomaly"]   for r in anomaly_results]
    df["anomaly_score"] = [r["score"]        for r in anomaly_results]
    df["anomaly_reason"]= [r["reason"]       for r in anomaly_results]
    df["anomaly_conf"]  = [r["confidence"]   for r in anomaly_results]

    anomaly_count = int(df["is_anomaly"].sum())
    print(f"   {anomaly_count} anomalies detected")

    print("\n   Stage 3: Predicting next 30 days...")
    transactions_list = df.to_dict("records")
    predictions = predict_all_categories(
        transactions_list,
        forecast_days=30
    )
    print(f"  Predictions ready for "
          f"{len(predictions)} categories")
    print("\n  Stage 4: Calculating health score...")
    total_debit  = round(float(df["debit"].sum()), 2)
    total_credit = round(float(df["credit"].sum()), 2)
    net_balance  = round(total_credit - total_debit, 2)
    category_summary = {}
    for cat in df["category"].unique():
        cat_df = df[df["category"] == cat]
        total  = float(cat_df["amount"].sum())
        category_summary[cat] = {
            "total":      round(total, 2),
            "count":      int(len(cat_df)),
            "percentage": round(
                total / float(df["amount"].sum()) * 100
                if df["amount"].sum() > 0 else 0, 1
            )
        }

    health = calculate_health_score(
        total_credit     = total_credit,
        total_debit      = total_debit,
        net_balance      = net_balance,
        anomaly_count    = anomaly_count,
        transaction_count= len(df),
        category_summary = category_summary
    )
    debit_df     = df[df["type"] == "debit"]
    top_category = ""
    if not debit_df.empty:
        top_category = debit_df\
            .groupby("category")["amount"]\
            .sum().idxmax()

    print(f"  Score: {health['score']}/100 "
          f"({health['grade']} — {health['grade_text']})")

    stats = {
        "total_debit":      total_debit,
        "total_credit":     total_credit,
        "net_balance":      net_balance,
        "savings_rate":     health["savings_rate"],
        "top_category":     top_category,
        "category_summary": category_summary,
        "health_score":     health["score"],
        "grade":            health["grade"],
        "grade_text":       health["grade_text"],
        "score_breakdown":  health["breakdown"],
        "tips":             health["tips"],
        "anomaly_count":    anomaly_count,
        "predictions":      predictions,
        "status":           "ready",
    }

    print(f"\n Pipeline complete!")
    print(f"   Debit:    ₹{total_debit:,.2f}")
    print(f"   Credit:   ₹{total_credit:,.2f}")
    print(f"   Balance:  ₹{net_balance:,.2f}")
    print(f"   Score:    {health['score']}/100")
    print(f"   Anomalies: {anomaly_count}")

    return df, stats