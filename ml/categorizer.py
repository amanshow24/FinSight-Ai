import joblib
import re
import os

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), 
    "../models/categorizer.pkl"
)

_model = None

def load_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def categorize(description):
    """
    Predict category for one transaction
    Returns: (category, confidence_score)
    """
    model  = load_model()
    clean  = preprocess(description)
    pred   = model.predict([clean])[0]
    proba  = model.predict_proba([clean])[0]
    conf   = round(float(max(proba)), 4)
    return pred, conf

def categorize_batch(descriptions):
    """
    Predict categories for a list of transactions
    Returns: list of (category, confidence) tuples
    """
    model   = load_model()
    cleaned = [preprocess(d) for d in descriptions]
    preds   = model.predict(cleaned)
    probas  = model.predict_proba(cleaned)
    results = [
        (preds[i], round(float(max(probas[i])), 4))
        for i in range(len(preds))
    ]
    return results