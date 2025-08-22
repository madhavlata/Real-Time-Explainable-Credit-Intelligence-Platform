# app/tasks.py
from datetime import datetime
from .inference import get_ticker_features, calculate_creditworthiness
from .database import save_score_data
from .config import TICKERS_TO_MONITOR

def run_daily_scoring_job():
    """
    Fetches data, calculates scores for all monitored tickers, and saves to the database.
    """
    print("🚀 Starting daily credit scoring job...")
    today_str = datetime.now().strftime('%Y-%m-%d')

    for ticker in TICKERS_TO_MONITOR:
        try:
            print(f"Processing ticker: {ticker}")
            # 1. Get features for today's date
            features = get_ticker_features(ticker, today_str)

            # 2. Calculate the creditworthiness score
            score = calculate_creditworthiness(features, method="weighted")

            # 3. Prepare data for storage
            # The NEW code in app/tasks.py
            score_data = {
                "ticker": ticker,
                "date": features['date'],
                "score": float(score),
                "features": {k: v for k, v in features.items() if k not in ['ticker', 'date']}
            }

            # 4. Save to MongoDB
            save_score_data(score_data)

        except Exception as e:
            print(f"❌ Failed to process {ticker}: {e}")

    print("✅ Daily credit scoring job finished.")