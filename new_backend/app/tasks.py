# app/tasks.py
from datetime import datetime
# Import the new, more powerful functions
from .inference import get_ticker_features, calculate_creditworthiness_with_explain
from .database import save_score_data
from .config import TICKERS_TO_MONITOR

def run_daily_scoring_job():
    """
    Fetches data, calculates scores with explanations for all monitored tickers, 
    and saves the detailed results to the database.
    """
    print("🚀 Starting daily credit scoring job with explanations...")
    today_str = datetime.now().strftime('%Y-%m-%d')

    for ticker in TICKERS_TO_MONITOR:
        try:
            print(f"Processing ticker: {ticker}")
            
            # 1. Get all features using the new logic
            features = get_ticker_features(ticker, today_str)
            features["ticker"] = ticker

            # 2. Calculate the score, probabilities, and SHAP explanations
            creditworthiness, probs, shap_metadata = calculate_creditworthiness_with_explain(features, method="weighted")

            # 3. Prepare the rich data object for storage
            score_data = {
                "ticker": ticker,
                "date": features['date'],
                "creditworthiness": creditworthiness,
                "risk_probs": probs,
                "shap_explanations": shap_metadata,
                "features": {k: v for k, v in features.items() if k not in ['ticker', 'date']}
            }

            # 4. Save the complete object to MongoDB
            save_score_data(score_data)

        except Exception as e:
            print(f"❌ Failed to process {ticker}: {e}")

    print("✅ Daily credit scoring job finished.")
