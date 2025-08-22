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

training_df = pd.read_csv("final training.csv", parse_dates=["date"])

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
        return {
            "de_ratio": 0.0, "current_ratio": 0.0, "quick_ratio": 0.0,
            "roa": 0.0, "roe": 0.0, "profit_margin": 0.0
        }

# -------------------- Sentiment & News -------------------- #
def get_company_name(stock_ticker: str) -> str:
    try:
        company = yf.Ticker(stock_ticker)
        return company.info.get("longName", "")
    except Exception:
        return ""

def fetch_company_news(company_name: str, date: str, window: int = 3, max_articles: int = 5) -> list:
    try:
        google_news = GNews(language="en", country="US", max_results=max_articles)
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = target_date - timedelta(days=window)
        end_date = target_date + timedelta(days=window)

        if start_date.date() == end_date.date():
            end_date += timedelta(days=1)

        google_news.start_date = (start_date.year, start_date.month, start_date.day)
        google_news.end_date = (end_date.year, end_date.month, end_date.day)

        news_results = google_news.get_news(company_name)
        return news_results[:max_articles] if news_results else []
    except Exception:
        return []

def analyze_sentiment_with_hf(news_data: list) -> float:
    if not news_data:
        return 0.0
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
    )
    total_score, count = 0, 0
    for article in news_data:
        try:
            text_to_analyze = f"{article.get('title', '')}. {article.get('description', '')}"
            sentiment = sentiment_pipeline(text_to_analyze)[0]
            label, score = sentiment["label"].upper(), sentiment["score"]
            mapped = score if label == "POSITIVE" else -score if label == "NEGATIVE" else 0.0
            total_score += mapped
            count += 1
        except Exception:
            continue
    return round(total_score / count, 4) if count > 0 else 0.0

# -------------------- Decayed Sentiment -------------------- #
def sentiment_decay(dates, sentiments, decay=0.8, scale=1.0):
    df = pd.DataFrame({"date": pd.to_datetime(dates), "sentiment": sentiments})
    df = df.sort_values("date").reset_index(drop=True)
    decayed_scores, prev_score = [], 0
    for _, row in df.iterrows():
        s = row["sentiment"]
        new_impact = s * scale
        current_score = prev_score * decay + new_impact
        decayed_scores.append(current_score)
        prev_score = current_score
    df["decayed_score"] = decayed_scores
    return df

def compute_sentiment_features(ticker: str, target_date: str, lookback_days: int = 5) -> tuple[float, float]:
    company_name = get_company_name(ticker)
    if not company_name:
        return 0.0, 0.0
    dates, sentiments = [], []
    for i in range(lookback_days, -1, -1):
        day = (pd.to_datetime(target_date) - timedelta(days=i)).strftime("%Y-%m-%d")
        news = fetch_company_news(company_name, day, window=0, max_articles=5)
        score = analyze_sentiment_with_hf(news)
        dates.append(day)
        sentiments.append(score)

    df = sentiment_decay(dates, sentiments, decay=0.8, scale=1.0)
    decayed_score = float(df["decayed_score"].iloc[-1])
    latest_raw_score = float(df["sentiment"].iloc[-1])
    return decayed_score, latest_raw_score

# -------------------- Technicals -------------------- #
def safe_get(series, date):
    val = series.loc[date]
    if isinstance(val, pd.Series):
        return float(val.iloc[-1] if not val.empty else 0.0)
    return float(val or 0.0)

def compute_features_for_inference(df: pd.DataFrame, fundamentals: dict, target_date: str) -> dict:
    df = df.sort_index()
    df = df[~df.index.duplicated(keep='last')]
    close = df["Adj Close"]
    dt_target = pd.to_datetime(target_date)

    df_filtered = df[df.index <= dt_target]
    if df_filtered.empty:
        raise ValueError(f"No trading data available on or before {target_date}")
    actual_date = df_filtered.index.max()

    vol_5d = close.pct_change().rolling(5).std()
    vol_20d = close.pct_change().rolling(20).std()
    vol_60d = close.pct_change().rolling(60).std()
    rolling_max = close.rolling(60, min_periods=1).max()
    drawdown_60d = close / rolling_max - 1.0
    prev_return_5d = close.pct_change(5)
    prev_return_20d = close.pct_change(20)
    prev_return_60d = close.pct_change(60)

    features = {
        "vol_5d": safe_get(vol_5d, actual_date),
        "vol_20d": safe_get(vol_20d, actual_date),
        "vol_60d": safe_get(vol_60d, actual_date),
        "drawdown_60d": safe_get(drawdown_60d, actual_date),
        "prev_return_5d": safe_get(prev_return_5d, actual_date),
        "prev_return_20d": safe_get(prev_return_20d, actual_date),
        "prev_return_60d": safe_get(prev_return_60d, actual_date),
    }

    # Include fundamentals
    features.update({k: float(v or 0.0) for k, v in fundamentals.items()})

    features["date"] = actual_date.strftime('%Y-%m-%d')
    return features

def get_ticker_features(ticker: str, target_date: str, lookback_years: int = 2) -> dict:
    dt_target = pd.to_datetime(target_date)

    # Check if ticker & date exist in training CSV
    row = training_df[(training_df["ticker"] == ticker) & (training_df["date"] == dt_target)]
    if not row.empty:
        # Extract features directly from CSV
        features = row.iloc[0].to_dict()
        print("using csv")
        features['date'] = features['date'].strftime('%Y-%m-%d')
        # Ensure numeric fields are floats
        features = {k: float(v) if isinstance(v, (int, float, np.number)) else v for k, v in features.items()}
        return features

    # Otherwise, fetch from yfinance and compute
    df = yf.download(ticker, period=f"{lookback_years}y", interval="1d", auto_adjust=False, progress=False)
    fundamentals = fetch_fundamentals(ticker)
    features = compute_features_for_inference(df, fundamentals, target_date)

    # Add sentiment
    decayed_sentiment, _ = compute_sentiment_features(ticker, features["date"], lookback_days=5)
    features["decayed_sentiment"] = float(decayed_sentiment)
    return features

# -------------------- Models & Features -------------------- #
models = {
    "label_5d": joblib.load("./models/xgb_model_label_5d.pkl"),
    "label_20d": joblib.load("./models/xgb_model_label_20d.pkl"),
    "label_60d": joblib.load("./models/xgb_model_label_60d.pkl"),
}

feature_cols = [
    "vol_5d", "vol_20d", "vol_60d",
    "drawdown_60d", "de_ratio",
    "prev_return_5d", "prev_return_20d", "prev_return_60d",
    "decayed_sentiment"
]

scaler = joblib.load("./models/scaler.pkl")

# -------------------- Creditworthiness -------------------- #
def creditworthiness_from_prob(prob: float) -> float:
    prob = np.clip(prob, 1e-6, 1 - 1e-6)
    score = 800 / (1 + np.exp(5 * (prob - 0.5)))
    score = 300 + (score / 800) * 550
    return round(score, 2)

def calculate_creditworthiness_with_explain(features: dict, method: str = "weighted"):
    df = pd.DataFrame([features])
    X_scaled = scaler.transform(df[feature_cols])

    probs, shap_metadata = {}, {}
    for label, model in models.items():
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
    return creditworthiness, probs, shap_metadata

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
