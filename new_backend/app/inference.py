import pandas as pd
import yfinance as yf
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler

def get_nearest_trading_day(df, target_date):
    target_date = pd.to_datetime(target_date)
    available_dates = df.index
    nearest_date = available_dates[available_dates <= target_date].max()
    return nearest_date

# -------------------- Fundamentals -------------------- #
def fetch_fundamentals(ticker: str) -> dict:
    """Fetch multiple fundamental ratios from Yahoo Finance."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "de_ratio": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "roa": info.get("returnOnAssets"),
            "roe": info.get("returnOnEquity"),
            "profit_margin": info.get("profitMargins"),
        }
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return {
            "de_ratio": None,
            "current_ratio": None,
            "quick_ratio": None,
            "roa": None,
            "roe": None,
            "profit_margin": None,
        }

# -------------------- Feature Calculation -------------------- #
def compute_features_for_inference(df: pd.DataFrame, ticker: str, fundamentals: dict, target_date: str) -> dict:
    df = df.sort_index()
    close = df["Adj Close"]

    if target_date not in close.index.strftime('%Y-%m-%d'):
        nearest_date = get_nearest_trading_day(close, target_date)
        if pd.isna(nearest_date):
            raise ValueError(f"No trading data available near {target_date} for {ticker}")
        print(f"Using nearest trading day: {nearest_date.strftime('%Y-%m-%d')} instead of {target_date}")
        target_date = nearest_date.strftime('%Y-%m-%d')

    # Volatility
    vol_5d = close.pct_change().rolling(5).std()
    vol_20d = close.pct_change().rolling(20).std()
    vol_60d = close.pct_change().rolling(60).std()

    # Max drawdown
    rolling_max = close.rolling(60, min_periods=1).max()
    drawdown_60d = close / rolling_max - 1.0

    # Previous returns
    prev_return_5d = close.pct_change(5)
    prev_return_20d = close.pct_change(20)
    prev_return_60d = close.pct_change(60)

    # Get feature values for the target date
    date_idx = close.index.get_loc(pd.to_datetime(target_date))

    # The NEW code in app/inference.py
# By wrapping each value in float(), we convert it from a Pandas/NumPy type
# to a standard Python float that MongoDB can understand.
    features = {
        "date": target_date,
        "ticker": ticker,
        "close": float(close.iloc[date_idx]),
        "vol_5d": float(vol_5d.iloc[date_idx]),
        "vol_20d": float(vol_20d.iloc[date_idx]),
        "vol_60d": float(vol_60d.iloc[date_idx]),
        "drawdown_60d": float(drawdown_60d.iloc[date_idx]),
        "prev_return_5d": float(prev_return_5d.iloc[date_idx]),
        "prev_return_20d": float(prev_return_20d.iloc[date_idx]),
        "prev_return_60d": float(prev_return_60d.iloc[date_idx]),
    }

    # Add fundamentals
    features.update(fundamentals)

    return features

def get_ticker_features(ticker: str, target_date: str, lookback_years: int = 2) -> dict:
    df = yf.download(ticker, period=f"{lookback_years}y", interval="1d", auto_adjust=False)
    if df.empty:
        raise ValueError(f"No data fetched for {ticker}.")
    fundamentals = fetch_fundamentals(ticker)
    features = compute_features_for_inference(df, ticker, fundamentals, target_date)
    return features

# -------------------- Load Models -------------------- #
models = {
    "label_5d": joblib.load("./models/xgb_model_label_5d.pkl"),
    "label_20d": joblib.load("./models/xgb_model_label_20d.pkl"),
    "label_60d": joblib.load("./models/xgb_model_label_60d.pkl"),
}

feature_cols = [
    "close", "vol_5d", "vol_20d", "vol_60d",
    "drawdown_60d", "de_ratio",
    "current_ratio", "quick_ratio",
    "roa", "roe", "profit_margin",
    "prev_return_5d", "prev_return_20d", "prev_return_60d"
]

# -------------------- Creditworthiness Calculation -------------------- #
def calculate_creditworthiness(features: dict, method: str = "weighted") -> float:
    df = pd.DataFrame([features])

    # Load the fitted scaler
    scaler = joblib.load("./models/scaler.pkl")
    X_scaled = scaler.transform(df[feature_cols])  # use transform, not fit_transform

    probs = [model.predict_proba(X_scaled)[:, 1][0] for model in models.values()]

    if method == "weighted":
        weights = {"label_5d": 0.3, "label_20d": 0.4, "label_60d": 0.3}
        avg_prob = sum(p * w for p, w in zip(probs, weights.values()))
    elif method == "geometric":
        avg_prob = np.prod(probs) ** (1 / len(probs))
    elif method == "exponential":
        avg_prob = np.mean(probs) ** 1.5
    else:
        avg_prob = np.mean(probs)

    creditworthiness = 100 - (avg_prob * 100)
    return creditworthiness

# -------------------- Example Usage -------------------- #
if __name__ == "__main__":
    ticker = "AMZN"
    target_date = "2025-03-20"

    features = get_ticker_features(ticker, target_date)
    score = calculate_creditworthiness(features, method="weighted")
    print(f"Creditworthiness for {ticker} on {target_date}: {score:.2f}")
