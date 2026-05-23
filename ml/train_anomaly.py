import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

print("=" * 50)
print("  FinSense AI — Training Anomaly Detector")
print("=" * 50)
print("\nGenerating training data...")

np.random.seed(42)
normal_data = []
for _ in range(200):
    normal_data.append({
        "amount":      np.random.uniform(50, 800),
        "hour":        np.random.choice(
                         [7,8,9,12,13,14,19,20,21]
                       ),
        "day_of_week": np.random.randint(0, 7),
        "label":       1  
    })
for _ in range(150):
    normal_data.append({
        "amount":      np.random.uniform(200, 5000),
        "hour":        np.random.choice(
                         [10,11,12,14,15,16,17,18]
                       ),
        "day_of_week": np.random.randint(0, 7),
        "label":       1
    })
for _ in range(50):
    normal_data.append({
        "amount":      np.random.uniform(15000, 80000),
        "hour":        np.random.choice([9, 10, 11]),
        "day_of_week": np.random.randint(0, 5),
        "label":       1
    })

for _ in range(100):
    normal_data.append({
        "amount":      np.random.uniform(500, 3000),
        "hour":        np.random.choice([9,10,11,14,15]),
        "day_of_week": np.random.randint(0, 7),
        "label":       1
    })


for _ in range(100):
    normal_data.append({
        "amount":      np.random.uniform(3000, 25000),
        "hour":        np.random.choice([9, 10]),
        "day_of_week": np.random.randint(0, 5),
        "label":       1
    })

anomaly_data = []
for _ in range(30):
    anomaly_data.append({
        "amount":      np.random.uniform(50000, 200000),
        "hour":        np.random.choice([2, 3, 4]),
        "day_of_week": np.random.randint(0, 7),
        "label":       -1 
    })
for _ in range(20):
    anomaly_data.append({
        "amount":      np.random.uniform(1, 10),
        "hour":        np.random.choice([1, 2, 3, 4]),
        "day_of_week": np.random.randint(0, 7),
        "label":       -1
    })

for _ in range(20):
    anomaly_data.append({
        "amount":      np.random.uniform(100000, 500000),
        "hour":        np.random.choice([0, 1, 23]),
        "day_of_week": np.random.randint(0, 7),
        "label":       -1
    })

all_data = normal_data + anomaly_data
df = pd.DataFrame(all_data)
print(f" Total samples:   {len(df)}")
print(f" Normal:          {len(normal_data)}")
print(f"Anomalies:       {len(anomaly_data)}")
print("\n🔧 Engineering features...")

def engineer_features(df):
    features = pd.DataFrame()
    mean_amt = df["amount"].mean()
    std_amt  = df["amount"].std()
    features["amount_zscore"] = (
        df["amount"] - mean_amt
    ) / (std_amt + 1e-9)
    features["amount_log"] = np.log1p(df["amount"])

    features["hour"] = df["hour"]
    features["is_late_night"] = df["hour"].apply(
        lambda h: 1 if h >= 23 or h <= 5 else 0
    )
    features["day_of_week"] = df["day_of_week"]

    features["is_weekend"] = df["day_of_week"].apply(
        lambda d: 1 if d >= 5 else 0
    )
    features["amount_category"] = df["amount"].apply(
        lambda a: 0 if a < 500
             else 1 if a < 5000
             else 2 if a < 50000
             else 3
    )

    return features

X = engineer_features(df)
y = df["label"]

print(f" Features created: {X.columns.tolist()}")

print("\nTraining Isolation Forest...")

model = Pipeline([
    ("scaler", StandardScaler()),
    ("iso",    IsolationForest(
        n_estimators=200,
        contamination=0.05,  # 5% anomaly rate
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    ))
])

X_normal = X[y == 1]
model.fit(X_normal)
print(" Training complete!")
print("\n Evaluating model...")

predictions = model.predict(X)
scores      = model.decision_function(X)
true_normal   = sum((y == 1) & (predictions == 1))
true_anomaly  = sum((y == -1) & (predictions == -1))
false_normal  = sum((y == -1) & (predictions == 1))
false_anomaly = sum((y == 1) & (predictions == -1))

total     = len(y)
accuracy  = (true_normal + true_anomaly) / total * 100
precision = true_anomaly / (true_anomaly + false_anomaly + 1e-9) * 100
recall    = true_anomaly / (true_anomaly + false_normal + 1e-9) * 100

print(f"\n{'='*50}")
print(f"  ACCURACY:  {accuracy:.1f}%")
print(f"  PRECISION: {precision:.1f}%")
print(f"  RECALL:    {recall:.1f}%")
print(f"{'='*50}")

print(f"\n  True Normal:    {true_normal}")
print(f"  True Anomaly:   {true_anomaly}")
print(f"  False Normal:   {false_normal}")
print(f"  False Anomaly:  {false_anomaly}")
print("\n Testing with real examples:")

test_cases = [
    {"desc": "Zomato order ₹350 at 1PM",
     "amount": 350,   "hour": 13, "day": 2},
    {"desc": "Salary ₹45000 at 10AM",
     "amount": 45000, "hour": 10, "day": 1},
    {"desc": "₹95000 transfer at 3AM 🚨",
     "amount": 95000, "hour": 3,  "day": 4},
    {"desc": "Netflix ₹649 at 8PM",
     "amount": 649,   "hour": 20, "day": 6},
    {"desc": "₹2,00,000 at 2AM 🚨",
     "amount": 200000,"hour": 2,  "day": 3},
    {"desc": "Electricity bill ₹1200",
     "amount": 1200,  "hour": 10, "day": 1},
    {"desc": "₹5 transfer at 4AM 🚨",
     "amount": 5,     "hour": 4,  "day": 0},
    {"desc": "Amazon ₹2999 at 3PM",
     "amount": 2999,  "hour": 15, "day": 5},
]

test_df = pd.DataFrame([{
    "amount":      t["amount"],
    "hour":        t["hour"],
    "day_of_week": t["day"]
} for t in test_cases])

test_features = engineer_features(test_df)
test_preds    = model.predict(test_features)
test_scores   = model.decision_function(test_features)

for i, case in enumerate(test_cases):
    pred      = test_preds[i]
    score     = test_scores[i]
    is_anomaly = pred == -1
    conf      = round(abs(score) * 100, 1)
    status    = " ANOMALY" if is_anomaly else " Normal "
    print(f"  {status} | {case['desc']:<35} | score: {score:.3f}")
print("\n Saving model...")

os.makedirs("../models", exist_ok=True)


joblib.dump(model, "../models/anomaly_model.pkl")

import json
metadata = {
    "amount_mean": float(df["amount"].mean()),
    "amount_std":  float(df["amount"].std()),
    "contamination": 0.05,
    "features": [
        "amount_zscore", "amount_log",
        "hour", "is_late_night",
        "day_of_week", "is_weekend",
        "amount_category"
    ],
    "version": "1.0"
}
with open("../models/anomaly_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(" Saved: models/anomaly_model.pkl")
print("Saved: models/anomaly_metadata.json")
print("\n Anomaly detector ready!")
