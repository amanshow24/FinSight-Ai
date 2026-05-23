from flask_restx import Namespace, Resource
from flask import request
from services.auth_service import token_required
from services.pdf_parser import parse_bank_statement
from services.firebase_service import (
    save_statement, update_statement,
    get_statement, save_transactions,
    upload_to_storage, delete_from_storage
)
import tempfile, os

stmt_ns = Namespace("statement", description="Bank Statement Analysis")

ALLOWED_EXTENSIONS = {"pdf", "csv"}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ════════════════════════════
#   POST /statement/upload
# ════════════════════════════
@stmt_ns.route("/upload")
class StatementUpload(Resource):
    @token_required
    def post(self):
        """Upload a bank statement PDF or CSV"""

        # Check file in request
        if "file" not in request.files:
            return {"message": "No file uploaded"}, 400

        file = request.files["file"]

        if file.filename == "":
            return {"message": "No file selected"}, 400

        if not allowed_file(file.filename):
            return {"message": "Only PDF and CSV files allowed"}, 400

        try:
            user_id = request.uid

            # Save file temporarily
            suffix = "." + file.filename.rsplit(".", 1)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

            # Parse the statement
            df, bank = parse_bank_statement(tmp_path)

            if df is None:
                os.unlink(tmp_path)
                return {"message": f"Could not parse file: {bank}"}, 422

            # Save statement record to Firestore
            stmt_id = save_statement(user_id, bank, len(df))

            # Save all transactions to Firestore
            save_transactions(stmt_id, user_id, df)

            # Calculate basic stats
            total_debit  = round(float(df["debit"].sum()), 2)
            total_credit = round(float(df["credit"].sum()), 2)

            # Update statement with stats
            update_statement(stmt_id, {
                "status":        "ready",
                "total_debit":   total_debit,
                "total_credit":  total_credit,
                "bank_name":     bank,
            })

            # Delete temp file (security)
            os.unlink(tmp_path)

            return {
                "message":      "Statement uploaded and analyzed!",
                "statement_id": stmt_id,
                "bank":         bank,
                "transactions":  len(df),
                "total_debit":   total_debit,
                "total_credit":  total_credit,
                "status":        "ready"
            }, 200

        except Exception as e:
            return {"message": f"Upload failed: {str(e)}"}, 500


# ════════════════════════════
#   GET /statement/{id}/summary
# ════════════════════════════
@stmt_ns.route("/<string:stmt_id>/summary")
class StatementSummary(Resource):
    @token_required
    def get(self, stmt_id):
        """Get summary of an analyzed statement"""
        try:
            stmt = get_statement(stmt_id)

            if not stmt:
                return {"message": "Statement not found"}, 404

            # Security — only owner can view
            if stmt["user_id"] != request.uid:
                return {"message": "Unauthorized"}, 403

            return {
                "statement_id":      stmt_id,
                "bank":              stmt.get("bank_name"),
                "status":            stmt.get("status"),
                "transactions":      stmt.get("transactions_count"),
                "total_debit":       stmt.get("total_debit"),
                "total_credit":      stmt.get("total_credit"),
                "health_score":      stmt.get("health_score", 0),
                "created_at":        stmt.get("created_at"),
            }, 200

        except Exception as e:
            return {"message": str(e)}, 500