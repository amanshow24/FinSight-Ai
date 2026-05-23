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