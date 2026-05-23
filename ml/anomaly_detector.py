import joblib
import json
import numpy as np
import pandas as pd
import os

MODEL_PATH    = os.path.join(
    os.path.dirname(__file__), "../models/anomaly_model.pkl"
)
METADATA_PATH = os.path.join(
    os.path.dirname(__file__), "../models/anomaly_metadata.json"
)
_model    = None
_metadata = None

def load_model():
    global _model, _metadata
    if _model is None:
        _model    = joblib.load(MODEL_PATH)
        with open(METADATA_PATH) as f:
            _metadata = json.load(f)
    return _model, _metadata


def engineer_features(df):
    features = pd.DataFrame()
    features["amount_zscore"]   = (
        df["amount"] - df["amount"].mean()
    ) / (df["amount"].std() + 1e-9)
    features["amount_log"]      = np.log1p(df["amount"])
    features["hour"]            = df["hour"]
    features["is_late_night"]   = df["hour"].apply(
        lambda h: 1 if h >= 23 or h <= 5 else 0
    )
    features["day_of_week"]     = df["day_of_week"]
    features["is_weekend"]      = df["day_of_week"].apply(
        lambda d: 1 if d >= 5 else 0
    )
    features["amount_category"] = df["amount"].apply(
        lambda a: 0 if a < 500
             else 1 if a < 5000
             else 2 if a < 50000
             else 3
    )
    return features


def detect_anomaly(amount, hour, day_of_week):
    """
    Detect if single transaction is anomalous
    Returns: (is_anomaly, score, confidence, reason)
    """
    model, _ = load_model()

    df = pd.DataFrame([{
        "amount":      amount,
        "hour":        hour,
        "day_of_week": day_of_week
    }])

    features   = engineer_features(df)
    prediction = model.predict(features)[0]
    score      = model.decision_function(features)[0]

    is_anomaly = prediction == -1
    confidence = round(min(abs(score) * 100, 99.9), 1)
    reason = ""
    if is_anomaly:
        if hour >= 23 or hour <= 5:
            reason = "Unusual transaction time (late night)"
        elif amount > 50000:
            reason = "Very large transaction amount"
        elif amount < 10:
            reason = "Suspiciously small amount"
        else:
            reason = "Unusual spending pattern detected"

    return {
        "is_anomaly": bool(is_anomaly),
        "score":      round(float(score), 4),
        "confidence": confidence,
        "reason":     reason
    }


def detect_batch(transactions):
    """
    Detect anomalies in a list of transactions
    Input: list of dicts with amount, hour, day_of_week
    Returns: list of anomaly results
    """
    model, _ = load_model()

    df       = pd.DataFrame(transactions)
    features = engineer_features(df)
    preds    = model.predict(features)
    scores   = model.decision_function(features)

    results = []
    for i in range(len(transactions)):
        is_anomaly = preds[i] == -1
        score      = scores[i]
        confidence = round(min(abs(score) * 100, 99.9), 1)
        hour       = transactions[i]["hour"]
        amount     = transactions[i]["amount"]

        reason = ""
        if is_anomaly:
            if hour >= 23 or hour <= 5:
                reason = "Unusual transaction time (late night)"
            elif amount > 50000:
                reason = "Very large transaction amount"
            elif amount < 10:
                reason = "Suspiciously small amount"
            else:
                reason = "Unusual spending pattern detected"

        results.append({
            "is_anomaly": bool(is_anomaly),
            "score":      round(float(score), 4),
            "confidence": confidence,
            "reason":     reason
        })

    return results