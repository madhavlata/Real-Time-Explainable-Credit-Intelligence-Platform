# final_inference.py
import os
import json
import pandas as pd
import yfinance as yf
import numpy as np
import joblib
import shap
from gnews import GNews
from transformers import pipeline
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- START: MEMORY OPTIMIZATION ---
# Load memory-intensive models ONCE when the application starts.
# These will be stored in memory and reused for all requests.

print("Loading pre-trained models into memory...")

# 1. Load the sentiment analysis pipeline globally
SENTIMENT_PIPELINE = pipeline(
    "sentiment-analysis",
    model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
)

# 2. Load ML models and scaler globally
MODELS = {
    "label_5d": joblib.load("./models/xgb_model_label_5d.pkl"),
    "label_20d": joblib.load("./models/xgb_model_label_20d.pkl"),
    "label_60d": joblib.load("./models/xgb_model_label_60d.pkl"),
}
SCALER = joblib.load("./models/scaler.pkl")

# 3. Load other resources globally
TRAINING_DF = pd.read_csv("final training.csv", parse_dates=["date"])
load_dotenv()

print("Models loaded successfully.")
# --- END: MEMORY OPTIMIZATION ---


# -------------------- Fundamentals -------------------- #
def fetch_fundamentals(ticker: str) -> dict:
    # ... (no changes to this function)
    try:
        info = yf.Ticker(ticker).info
        return {
            "de_ratio": info.get("debtToEquity", 0.0),
            "current_ratio": info.get("currentRatio", 0.0),
            "quick_ratio": info.get("quickRatio", 0.0),
            "roa": info.get("returnOnAssets", 0.0),
            "roe": info.get("returnOnEquity", 0.0),
            "profit_margin": info.get("profitMargins", 0.0),
        }
    except Exception:
        return {
            "de_ratio": 0.0, "current_ratio": 0.0, "quick_ratio": 0.0,
            "roa": 0.0, "roe": 0.0, "profit_margin": 0.0
        }

# -------------------- Sentiment & News (Updated) -------------------- #
# ... (get_company_name and fetch_company_news remain the same)

def analyze_sentiment_with_hf(news_data: list) -> float:
    """Uses the globally loaded sentiment pipeline."""
    if not news_data:
        return 0.0
    
    total_score, count = 0, 0
    for article in news_data:
        try:
            text_to_analyze = f"{article.get('title', '')}. {article.get('description', '')}"
            # --- CHANGE: Use the global pipeline ---
            sentiment = SENTIMENT_PIPELINE(text_to_analyze)[0]
            label, score = sentiment["label"].upper(), sentiment["score"]
            mapped = score if label == "POSITIVE" else -score if label == "NEGATIVE" else 0.0
            total_score += mapped
            count += 1
        except Exception:
            continue
    return round(total_score / count, 4) if count > 0 else 0.0

# ... (sentiment_decay and compute_sentiment_features remain the same)
# ... (technicals and feature computation functions remain the same)

def get_ticker_features(ticker: str, target_date: str, lookback_years: int = 2) -> dict:
    dt_target = pd.to_datetime(target_date)
    # --- CHANGE: Use the global TRAINING_DF ---
    row = TRAINING_DF[(TRAINING_DF["ticker"] == ticker) & (TRAINING_DF["date"] == dt_target)]
    if not row.empty:
        features = row.iloc[0].to_dict()
        print("using csv")
        features['date'] = features['date'].strftime('%Y-%m-%d')
        features = {k: float(v) if isinstance(v, (int, float, np.number)) else v for k, v in features.items()}
        return features

    df = yf.download(ticker, period=f"{lookback_years}y", interval="1d", auto_adjust=False, progress=False)
    fundamentals = fetch_fundamentals(ticker)
    features = compute_features_for_inference(df, fundamentals, target_date)
    decayed_sentiment, _ = compute_sentiment_features(ticker, features["date"], lookback_days=5)
    features["decayed_sentiment"] = float(decayed_sentiment)
    return features


# -------------------- Models & Features (Updated) -------------------- #
feature_cols = [
    "vol_5d", "vol_20d", "vol_60d",
    "drawdown_60d", "de_ratio",
    "prev_return_5d", "prev_return_20d", "prev_return_60d",
    "decayed_sentiment"
]

# -------------------- Creditworthiness (Updated) -------------------- #
# ... (creditworthiness_from_prob remains the same)

def calculate_creditworthiness_with_explain(features: dict, method: str = "weighted"):
    df = pd.DataFrame([features])
    # --- CHANGE: Use the global SCALER ---
    X_scaled = SCALER.transform(df[feature_cols])

    probs, shap_metadata = {}, {}
    # --- CHANGE: Use the global MODELS ---
    for label, model in MODELS.items():
        prob = model.predict_proba(X_scaled)[:, 1][0]
        probs[label] = float(prob)
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_scaled)
        shap_metadata[label] = {
            "base_value": float(explainer.expected_value),
            "feature_values": {f: float(v) for f, v in zip(feature_cols, X_scaled[0])},
            "shap_values": {f: float(v) for f, v in zip(feature_cols, shap_values[0])}
        }

    if method == "weighted":
        weights = {"label_5d": 0.3, "label_20d": 0.4, "label_60d": 0.3}
        avg_prob = sum(probs[label] * weights[label] for label in probs)
    else:
        avg_prob = np.mean(list(probs.values()))

    creditworthiness = creditworthiness_from_prob(avg_prob)
    summary = generate_shap_summary(shap_metadata, creditworthiness, features.get("ticker", "this company"))
    return creditworthiness, probs, shap_metadata, summary


def calculate_creditworthiness_with_explain_json(features: dict, method: str = "weighted"):
    # Keep strings as-is, numeric as float
    features = {k: float(v) if isinstance(v, (int, float, np.number)) else v for k, v in features.items()}
    creditworthiness, probs, shap_metadata = calculate_creditworthiness_with_explain(features, method)
    return json.dumps({
        "ticker": features.get("ticker", ""),
        "date": features.get("date", ""),
        "creditworthiness": creditworthiness,
        "risk_probs": probs,
        "shap_explanations": shap_metadata
    }, indent=2)

# -------------------- Example -------------------- #
if __name__ == "__main__":
    ticker = "AAPL"
    target_date = "2025-08-22"

    print(f"Fetching features for {ticker} on {target_date}...")
    features = get_ticker_features(ticker, target_date)
    features["ticker"] = ticker
    print("Features fetched. Calculating creditworthiness...")
    result_json = calculate_creditworthiness_with_explain_json(features, method="weighted")
    print(result_json)
