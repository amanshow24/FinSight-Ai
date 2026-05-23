from firebase_admin import firestore, storage
from datetime import datetime
import uuid

db = firestore.client()

def create_user(uid, email, name):
    db.collection("users").document(uid).set({
        "id":         uid,
        "email":      email,
        "name":       name,
        "created_at": datetime.utcnow().isoformat(),
        "statements": []
    })
    return True

def get_user(uid):
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None

def save_statement(user_id, bank_name, transactions_count):
    stmt_id = str(uuid.uuid4())
    db.collection("statements").document(stmt_id).set({
        "id":                 stmt_id,
        "user_id":            user_id,
        "bank_name":          bank_name,
        "transactions_count": transactions_count,
        "status":             "processing",
        "created_at":         datetime.utcnow().isoformat(),
        "total_debit":        0.0,
        "total_credit":       0.0,
        "net_balance":        0.0,
        "health_score":       0,
        "grade":              "N/A",
        "top_category":       "",
    })
    return stmt_id

def update_statement(stmt_id, data):
    db.collection("statements").document(stmt_id).update(data)

def get_statement(stmt_id):
    doc = db.collection("statements").document(stmt_id).get()
    return doc.to_dict() if doc.exists else None

def save_transactions(stmt_id, user_id, df):
    """Save all transactions using batch write"""
    batch = db.batch()
    count = 0

    for _, row in df.iterrows():
        txn_ref = db.collection("transactions").document()
        batch.set(txn_ref, {
            "statement_id":       stmt_id,
            "user_id":            user_id,
            "date":               str(row.get("date", "")),
            "description":        str(row.get("description", "")),
            "debit":              float(row.get("debit", 0)),
            "credit":             float(row.get("credit", 0)),
            "balance":            float(row.get("balance", 0)),
            "amount":             float(row.get("amount", 0)),
            "type":               str(row.get("type", "debit")),
            "category":           str(row.get("category", "Miscellaneous")),
            "category_confidence": float(row.get("confidence", 0.0)),
            "is_anomaly":         False,
            "anomaly_score":      0.0,
            "user_corrected":     False,
            "created_at":         datetime.utcnow().isoformat(),
        })
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()

    batch.commit()
    return True

def get_transactions(stmt_id):
    """Get all transactions for a statement"""
    docs = db.collection("transactions")\
             .where("statement_id", "==", stmt_id)\
             .stream()
    return [doc.to_dict() for doc in docs]

def get_transactions_by_category(stmt_id):
    """Get transactions grouped by category"""
    transactions = get_transactions(stmt_id)
    grouped = {}
    for txn in transactions:
        cat = txn.get("category", "Miscellaneous")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(txn)
    return grouped
def upload_to_storage(file_path, user_id, filename):
    bucket   = storage.bucket()
    blob_path = f"statements/{user_id}/{filename}"
    blob     = bucket.blob(blob_path)
    blob.upload_from_filename(file_path)
    return blob_path

def delete_from_storage(blob_path):
    try:
        bucket = storage.bucket()
        blob   = bucket.blob(blob_path)
        blob.delete()
    except:
        pass