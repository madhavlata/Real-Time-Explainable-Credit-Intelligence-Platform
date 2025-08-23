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
from functools import lru_cache

# -------------------- Setup -------------------- #
load_dotenv()
print("Initializing inference backend (optimized for memory)...")

# Load models/scaler once (small enough to keep resident)
MODELS = {
    "label_5d": joblib.load("./models/xgb_model_label_5d.pkl"),
    "label_20d": joblib.load("./models/xgb_model_label_20d.pkl"),
    "label_60d": joblib.load("./models/xgb_model_label_60d.pkl"),
}
SCALER = joblib.load("./models/scaler.pkl")

# -------------------- Lazy Loads -------------------- #
@lru_cache(maxsize=1)
def get_sentiment_pipeline():
    """Load HuggingFace transformer pipeline once, only on first use."""
    print("Loading HF sentiment pipeline into memory...")
    return pipeline(
        "sentiment-analysis",
        model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
    )

def load_training_row(ticker: str, dt_target: pd.Timestamp):
    """
    Load only the row you need from CSV instead of keeping entire file in memory.
    Assumes 'final training.csv' has a 'ticker' and 'date' column.
    """
    try:
        for chunk in pd.read_csv("final training.csv", parse_dates=["date"], chunksize=5000):
            row = chunk[(chunk["ticker"] == ticker) & (chunk["date"] == dt_target)]
            if not row.empty:
                return row.iloc[0].to_dict()
    except FileNotFoundError:
        return None
    return None

# -------------------- Fundamentals -------------------- #
def fetch_fundamentals(ticker: str) -> dict:
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
        return {k: 0.0 for k in ["de_ratio", "current_ratio", "quick_ratio", "roa", "roe", "profit_margin"]}

# -------------------- Sentiment -------------------- #
def analyze_sentiment_with_hf(news_data: list) -> float:
    """Run sentiment analysis with lazy-loaded HF pipeline."""
    if not news_data:
        return 0.0
    
    pipeline_obj = get_sentiment_pipeline()
    total_score, count = 0, 0
    for article in news_data:
        try:
            text_to_analyze = f"{article.get('title', '')}. {article.get('description', '')}"
            sentiment = pipeline_obj(text_to_analyze)[0]
            label, score = sentiment["label"].upper(), sentiment["score"]
            mapped = score if label == "POSITIVE" else -score if label == "NEGATIVE" else 0.0
            total_score += mapped
            count += 1
        except Exception:
            continue
    return round(total_score / count, 4) if count > 0 else 0.0

# -------------------- Features -------------------- #
def get_ticker_features(ticker: str, target_date: str, lookback_years: int = 2) -> dict:
    dt_target = pd.to_datetime(target_date)

    row = load_training_row(ticker, dt_target)
    if row:
        features = row
        features['date'] = features['date'].strftime('%Y-%m-%d')
        features = {k: float(v) if isinstance(v, (int, float, np.number)) else v for k, v in features.items()}
        return features

    # Fallback: build features on the fly
    df = yf.download(ticker, period=f"{lookback_years}y", interval="1d", auto_adjust=False, progress=False)
    fundamentals = fetch_fundamentals(ticker)
    features = compute_features_for_inference(df, fundamentals, target_date)
    decayed_sentiment, _ = compute_sentiment_features(ticker, features["date"], lookback_days=5)
    features["decayed_sentiment"] = float(decayed_sentiment)
    return features

feature_cols = [
    "vol_5d", "vol_20d", "vol_60d",
    "drawdown_60d", "de_ratio",
    "prev_return_5d", "prev_return_20d", "prev_return_60d",
    "decayed_sentiment"
]

# -------------------- Creditworthiness -------------------- #
def calculate_creditworthiness_with_explain(features: dict, method: str = "weighted", include_shap: bool = False):
    """
    Compute creditworthiness.
    include_shap=False (default) to avoid memory-heavy SHAP at runtime.
    """
    df = pd.DataFrame([features])
    X_scaled = SCALER.transform(df[feature_cols])

    probs, shap_metadata = {}, {}
    for label, model in MODELS.items():
        prob = model.predict_proba(X_scaled)[:, 1][0]
        probs[label] = float(prob)

        if include_shap:
            # SHAP is expensive, load only when explicitly needed
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

    if include_shap:
        summary = generate_shap_summary(shap_metadata, creditworthiness, features.get("ticker", "this company"))
    else:
        summary = "SHAP not included (set include_shap=True to compute)."

    return creditworthiness, probs, shap_metadata, summary

def calculate_creditworthiness_with_explain_json(features: dict, method: str = "weighted", include_shap: bool = False):
    features = {k: float(v) if isinstance(v, (int, float, np.number)) else v for k, v in features.items()}
    creditworthiness, probs, shap_metadata, summary = calculate_creditworthiness_with_explain(
        features, method, include_shap
    )
    return json.dumps({
        "ticker": features.get("ticker", ""),
        "date": features.get("date", ""),
        "creditworthiness": creditworthiness,
        "risk_probs": probs,
        "shap_explanations": shap_metadata,
        "summary": summary
    }, indent=2)

# -------------------- Example -------------------- #
if __name__ == "__main__":
    ticker = "AAPL"
    target_date = "2025-08-22"

    print(f"Fetching features for {ticker} on {target_date}...")
    features = get_ticker_features(ticker, target_date)
    features["ticker"] = ticker
    print("Features fetched. Calculating creditworthiness...")

    result_json = calculate_creditworthiness_with_explain_json(features, method="weighted", include_shap=False)
    print(result_json)
