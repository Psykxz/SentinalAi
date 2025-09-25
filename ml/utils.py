# import joblib
# import os

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# MODEL_PATH = os.path.join(BASE_DIR, "cyberbullying_model.pkl")

# # Load trained pipeline
# model = joblib.load(MODEL_PATH)

# def predict_text(text):
#     """Return prediction + probability from trained NLP model."""
#     pred = model.predict([text])[0]
#     prob = model.predict_proba([text])[0].max()
#     return {"label": pred, "confidence": round(prob, 2)}

import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "cyberbullying_model.pkl")

# Try loading trained model
model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    print(f"⚠️ Warning: Trained model not found at {MODEL_PATH}. Run train_model.py first.")

def predict_text(text):
    """Return prediction + probability from trained NLP model."""
    if model is None:
        return {"label": "Model not available", "confidence": 0.0}

    pred = model.predict([text])[0]
    prob = model.predict_proba([text])[0].max()
    return {"label": pred, "confidence": round(float(prob), 2)}
