import pandas as pd
import numpy as np
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)
from dataset import TRANSACTIONS

print("=" * 50)
print("  FinSense AI — Training Categorizer Model")
print("=" * 50)
print("\n Loading dataset...")
df = pd.DataFrame(TRANSACTIONS, columns=["description", "category"])
print(f" Total samples: {len(df)}")
print(f" Categories: {df['category'].nunique()}")
print("\nCategory distribution:")
print(df["category"].value_counts())
def preprocess(text):
    text = text.lower()
    import re
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

print("\n Preprocessing text...")
df["clean"] = df["description"].apply(preprocess)


# ── STEP 3: Split Dataset ─────────────────────
print("\n Splitting dataset (80% train, 20% test)...")
X = df["clean"]
y = df["category"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)
print(f" Training samples: {len(X_train)}")
print(f" Testing samples:  {len(X_test)}")
print("\n Building TF-IDF + Random Forest pipeline...")
model = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),   # unigrams + bigrams
        max_features=5000,
        min_df=1,
        sublinear_tf=True
    )),
    ("clf", RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1           
    ))
])
print("\nTraining model...")
model.fit(X_train, y_train)
print("Training complete!")
print("\nEvaluating model...")
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n{'='*50}")
print(f"  ACCURACY: {accuracy * 100:.2f}%")
if accuracy >= 0.88:
    print("  TARGET ACHIEVED! (88%+)")
else:
    print("   Below target — need more data")
print(f"{'='*50}")

print("\nDetailed Report:")
print(classification_report(y_test, y_pred))
print("\n Testing with real transaction examples:")
test_transactions = [
    "UPI/ZOMATO/ORDER123",
    "SALARY CREDIT",
    "NETFLIX SUBSCRIPTION",
    "ATM WITHDRAWAL",
    "APOLLO PHARMACY",
    "IRCTC TICKET BOOKING",
    "AMAZON PURCHASE",
    "SIP DEBIT ZERODHA",
    "COLLEGE FEE PAYMENT",
    "AIRTEL MOBILE RECHARGE",
]

for txn in test_transactions:
    clean = preprocess(txn)
    pred  = model.predict([clean])[0]
    proba = model.predict_proba([clean])[0]
    conf  = round(max(proba) * 100, 1)
    print(f"  {txn:<35} → {pred:<20} ({conf}% confident)")
print("\nSaving model...")
os.makedirs("../models", exist_ok=True)
joblib.dump(model, "../models/categorizer.pkl")
print(" Model saved: models/categorizer.pkl")
print("\nTraining complete! Ready for production.")