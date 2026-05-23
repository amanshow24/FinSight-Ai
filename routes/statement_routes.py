import pandas as pd
from flask_restx import Namespace, Resource
from flask import request
from services.auth_service import token_required
from services.pdf_parser import parse_bank_statement
from services.firebase_service import (
    save_statement, update_statement,
    get_statement, save_transactions,
    get_transactions, get_transactions_by_category
)
from services.pipeline import run_pipeline
import tempfile, os

stmt_ns = Namespace(
    "statement",
    description="Bank Statement Analysis"
)

ALLOWED = {"pdf", "csv"}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED

@stmt_ns.route("/upload")
class StatementUpload(Resource):
    @token_required
    def post(self):
        """Upload + parse + categorize bank statement"""

        if "file" not in request.files:
            return {"message": "No file uploaded"}, 400

        file = request.files["file"]

        if file.filename == "":
            return {"message": "No file selected"}, 400

        if not allowed_file(file.filename):
            return {"message": "Only PDF and CSV allowed"}, 400

        try:
            user_id = request.uid
            suffix = "." + file.filename.rsplit(".", 1)[1].lower()
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix
            ) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            print(f"\nParsing file: {file.filename}")
            df, bank = parse_bank_statement(tmp_path)

            if df is None:
                os.unlink(tmp_path)
                return {"message": f"Parse failed: {bank}"}, 422

            stmt_id = save_statement(user_id, bank, len(df))
            print(f"Statement ID: {stmt_id}")

            df, stats = run_pipeline(df, user_id, stmt_id)
            print(" Saving to Firestore...")
            save_transactions(stmt_id, user_id, df)
            update_statement(stmt_id, {
                "status":       stats["status"],
                "total_debit":  stats["total_debit"],
                "total_credit": stats["total_credit"],
                "net_balance":  stats["net_balance"],
                "health_score": stats["health_score"],
                "grade":        stats["grade"],
                "top_category": stats["top_category"],
                "bank_name":    bank,
            })
            os.unlink(tmp_path)

            return {
                "message":        " Statement analyzed!",
                "statement_id":   stmt_id,
                "bank":           bank,
                "transactions":   len(df),
                "total_debit":    stats["total_debit"],
                "total_credit":   stats["total_credit"],
                "net_balance":    stats["net_balance"],
                "health_score":   stats["health_score"],
                "grade":          stats["grade"],
                "top_category":   stats["top_category"],
                "status":         "ready"
            }, 200

        except Exception as e:
            print(f" Error: {str(e)}")
            return {"message": f"Failed: {str(e)}"}, 500
@stmt_ns.route("/<string:stmt_id>/summary")
class StatementSummary(Resource):
    @token_required
    def get(self, stmt_id):
        """Get statement summary"""
        try:
            stmt = get_statement(stmt_id)
            if not stmt:
                return {"message": "Not found"}, 404
            if stmt["user_id"] != request.uid:
                return {"message": "Unauthorized"}, 403

            return {
                "statement_id": stmt_id,
                "bank":         stmt.get("bank_name"),
                "status":       stmt.get("status"),
                "transactions": stmt.get("transactions_count"),
                "total_debit":  stmt.get("total_debit"),
                "total_credit": stmt.get("total_credit"),
                "net_balance":  stmt.get("net_balance"),
                "health_score": stmt.get("health_score"),
                "grade":        stmt.get("grade"),
                "top_category": stmt.get("top_category"),
                "created_at":   stmt.get("created_at"),
            }, 200

        except Exception as e:
            return {"message": str(e)}, 500
@stmt_ns.route("/<string:stmt_id>/categories")
class StatementCategories(Resource):
    @token_required
    def get(self, stmt_id):
        """Get all transactions grouped by category"""
        try:
            stmt = get_statement(stmt_id)
            if not stmt:
                return {"message": "Not found"}, 404
            if stmt["user_id"] != request.uid:
                return {"message": "Unauthorized"}, 403
            grouped = get_transactions_by_category(stmt_id)
            result = []
            for category, txns in grouped.items():
                total = sum(t["amount"] for t in txns)
                result.append({
                    "category":     category,
                    "total_amount": round(total, 2),
                    "count":        len(txns),
                    "transactions": [
                        {
                            "date":        t["date"],
                            "description": t["description"],
                            "amount":      t["amount"],
                            "type":        t["type"],
                            "confidence":  t["category_confidence"],
                        }
                        for t in sorted(
                            txns,
                            key=lambda x: x["date"]
                        )
                    ]
                })
            result = sorted(
                result,
                key=lambda x: x["total_amount"],
                reverse=True
            )

            return {
                "statement_id": stmt_id,
                "bank":         stmt.get("bank_name"),
                "categories":   result,
                "total":        len(result)
            }, 200

        except Exception as e:
            return {"message": str(e)}, 500
@stmt_ns.route("/<string:stmt_id>/transactions")
class StatementTransactions(Resource):
    @token_required
    def get(self, stmt_id):
        """Get all transactions for a statement"""
        try:
            stmt = get_statement(stmt_id)
            if not stmt:
                return {"message": "Not found"}, 404
            if stmt["user_id"] != request.uid:
                return {"message": "Unauthorized"}, 403

            txns = get_transactions(stmt_id)
            return {
                "statement_id": stmt_id,
                "count":        len(txns),
                "transactions": txns
            }, 200

        except Exception as e:
            return {"message": str(e)}, 500
@stmt_ns.route("/<string:stmt_id>/anomalies")
class StatementAnomalies(Resource):
    @token_required
    def get(self, stmt_id):
        """Get flagged anomalous transactions"""
        try:
            stmt = get_statement(stmt_id)
            if not stmt:
                return {"message": "Not found"}, 404
            if stmt["user_id"] != request.uid:
                return {"message": "Unauthorized"}, 403

            txns = get_transactions(stmt_id)

            # Filter only anomalies
            anomalies = [
                t for t in txns
                if t.get("is_anomaly") == True
            ]

            return {
                "statement_id":  stmt_id,
                "total_anomalies": len(anomalies),
                "anomalies": [
                    {
                        "date":        a["date"],
                        "description": a["description"],
                        "amount":      a["amount"],
                        "type":        a["type"],
                        "reason":      a.get("anomaly_reason",""),
                        "score":       a.get("anomaly_score", 0),
                    }
                    for a in anomalies
                ]
            }, 200

        except Exception as e:
            return {"message": str(e)}, 500
@stmt_ns.route("/<string:stmt_id>/prediction")
class StatementPrediction(Resource):
    @token_required
    def get(self, stmt_id):
        """Get 30-day spending forecast per category"""
        try:
            stmt = get_statement(stmt_id)
            if not stmt:
                return {"message": "Not found"}, 404
            if stmt["user_id"] != request.uid:
                return {"message": "Unauthorized"}, 403

            # Get transactions
            txns = get_transactions(stmt_id)
            if not txns:
                return {"message": "No transactions"}, 404

            # Run prediction
            from ml.predictor import predict_all_categories
            import sys, os
            sys.path.append(
                os.path.join(
                    os.path.dirname(__file__), "../ml"
                )
            )

            predictions = predict_all_categories(
                txns, forecast_days=30
            )

            # Build summary
            summary = []
            for cat, pred in predictions.items():
                summary.append({
                    "category":        cat,
                    "method":          pred["method"],
                    "predicted_total": pred["predicted_monthly_total"],
                    "daily_forecast":  pred["daily_forecast"][:7],
                    "lower_ci":        pred["lower_ci"][:7],
                    "upper_ci":        pred["upper_ci"][:7],
                })

            # Sort by predicted total
            summary = sorted(
                summary,
                key=lambda x: x["predicted_total"],
                reverse=True
            )

            return {
                "statement_id":   stmt_id,
                "forecast_days":  30,
                "predictions":    summary,
                "total_categories": len(summary),
                "note": "daily_forecast shows first 7 days"
            }, 200

        except Exception as e:
            return {"message": str(e)}, 500


@stmt_ns.route("/<string:stmt_id>/score")
class StatementScore(Resource):
    @token_required
    def get(self, stmt_id):
        """Get financial health score + grade + tips"""
        try:
            stmt = get_statement(stmt_id)
            if not stmt:
                return {"message": "Not found"}, 404
            if stmt["user_id"] != request.uid:
                return {"message": "Unauthorized"}, 403

            txns = get_transactions(stmt_id)

            # Recalculate from transactions
            df = pd.DataFrame(txns) if txns else pd.DataFrame()

            if df.empty:
                return {"message": "No data"}, 404

            total_debit  = round(float(df["debit"].sum()), 2)
            total_credit = round(float(df["credit"].sum()), 2)
            net_balance  = round(total_credit - total_debit, 2)
            anomaly_count = int(
                df["is_anomaly"].sum()
            ) if "is_anomaly" in df.columns else 0

            # Category summary
            cat_summary = {}
            if "category" in df.columns:
                for cat in df["category"].unique():
                    cat_df = df[df["category"] == cat]
                    total  = float(cat_df["amount"].sum())
                    cat_summary[cat] = {
                        "total":      round(total, 2),
                        "count":      int(len(cat_df)),
                        "percentage": round(
                            total /
                            float(df["amount"].sum()) * 100
                            if df["amount"].sum() > 0
                            else 0, 1
                        )
                    }

            import sys, os
            sys.path.append(
                os.path.join(
                    os.path.dirname(__file__), "../ml"
                )
            )
            from health_scorer import calculate_health_score

            health = calculate_health_score(
                total_credit      = total_credit,
                total_debit       = total_debit,
                net_balance       = net_balance,
                anomaly_count     = anomaly_count,
                transaction_count = len(df),
                category_summary  = cat_summary
            )

            return {
                "statement_id": stmt_id,
                "score":        health["score"],
                "grade":        health["grade"],
                "grade_text":   health["grade_text"],
                "savings_rate": health["savings_rate"],
                "breakdown": {
                    "savings_score":   health["breakdown"]["savings_score"],
                    "anomaly_score":   health["breakdown"]["anomaly_score"],
                    "stability_score": health["breakdown"]["stability_score"],
                    "budget_score":    health["breakdown"]["budget_score"],
                },
                "tips":         health["tips"],
                "summary": {
                    "total_credit":  total_credit,
                    "total_debit":   total_debit,
                    "net_balance":   net_balance,
                    "anomaly_count": anomaly_count,
                }
            }, 200

        except Exception as e:
            return {"message": str(e)}, 500
