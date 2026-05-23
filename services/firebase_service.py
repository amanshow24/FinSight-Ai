from firebase_admin import firestore, storage
from datetime import datetime
import uuid

db = firestore.client()

# ════════════════════════════
#   USER OPERATIONS
# ════════════════════════════

def create_user(uid, email, name):
    """Save new user to Firestore"""
    db.collection("users").document(uid).set({
        "id":          uid,
        "email":       email,
        "name":        name,
        "created_at":  datetime.utcnow().isoformat(),
        "statements":  []
    })
    return True

def get_user(uid):
    """Get user from Firestore"""
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict()
    return None

# ════════════════════════════
#   STATEMENT OPERATIONS
# ════════════════════════════

def save_statement(user_id, bank_name, transactions_count):
    """Create statement record in Firestore"""
    stmt_id = str(uuid.uuid4())
    db.collection("statements").document(stmt_id).set({
        "id":                   stmt_id,
        "user_id":              user_id,
        "bank_name":            bank_name,
        "transactions_count":   transactions_count,
        "status":               "processing",
        "created_at":           datetime.utcnow().isoformat(),
        "total_debit":          0,
        "total_credit":         0,
        "health_score":         0,
    })
    return stmt_id

def update_statement(stmt_id, data):
    """Update statement with analysis results"""
    db.collection("statements").document(stmt_id).update(data)

def get_statement(stmt_id):
    """Get statement from Firestore"""
    doc = db.collection("statements").document(stmt_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

def save_transactions(stmt_id, user_id, df):
    """Save all transactions to Firestore"""
    batch = db.batch()
    for _, row in df.iterrows():
        txn_ref = db.collection("transactions").document()
        batch.set(txn_ref, {
            "statement_id": stmt_id,
            "user_id":      user_id,
            "date":         str(row["date"]),
            "description":  str(row["description"]),
            "debit":        float(row["debit"]),
            "credit":       float(row["credit"]),
            "balance":      float(row["balance"]),
            "amount":       float(row["amount"]),
            "type":         str(row["type"]),
            "category":     "Uncategorized",
            "is_anomaly":   False,
        })
    batch.commit()
    return True

# ════════════════════════════
#   STORAGE OPERATIONS
# ════════════════════════════

def upload_to_storage(file_path, user_id, filename):
    """Upload file to Firebase Storage"""
    bucket = storage.bucket()
    blob_path = f"statements/{user_id}/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(file_path)
    return blob_path

def delete_from_storage(blob_path):
    """Delete file after parsing (security)"""
    bucket = storage.bucket()
    blob = bucket.blob(blob_path)
    blob.delete()