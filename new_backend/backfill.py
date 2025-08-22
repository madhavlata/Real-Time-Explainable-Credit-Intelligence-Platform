# backfill_historical_data.py

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

# Import functions and variables from your app
from app.config import TICKERS_TO_MONITOR
from app.inference import compute_features_for_inference, calculate_creditworthiness
from app.database import save_score_data

def run_historical_backfill():
    """
    Calculates and stores scores for the last 2 years for all monitored tickers.
    """
    print("🚀 Starting historical data backfill for the last 2 years.")

    # Define the date range for the backfill
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 2)

    for ticker in TICKERS_TO_MONITOR:
        print(f"\n--- Processing ticker: {ticker} ---")
        
        try:
            # Download a longer history (3 years) to ensure enough data for rolling calculations
            # at the beginning of our 2-year target period.
            print(f"Downloading 3 years of historical data for {ticker}...")
            hist_df = yf.download(ticker, period="3y", interval="1d", auto_adjust=False)
            
            if hist_df.empty:
                print(f"⚠️ No data found for {ticker}. Skipping.")
                continue

            # Generate the list of dates to process within the last 2 years
            dates_to_process = pd.date_range(start=start_date, end=end_date, freq='D')

            # Fetch fundamentals once per ticker
            from app.inference import fetch_fundamentals
            fundamentals = fetch_fundamentals(ticker)

            print(f"Calculating scores for {len(dates_to_process)} days...")
            for target_date in dates_to_process:
                target_date_str = target_date.strftime('%Y-%m-%d')
                
                try:
                    # Use the compute function directly, passing the downloaded dataframe
                    features = compute_features_for_inference(hist_df, ticker, fundamentals, target_date_str)
                    
                    score = calculate_creditworthiness(features, method="weighted")
                    
                    # The NEW code in backfill.py
                    score_data = {
                        "ticker": ticker,
                        "date": features['date'],
                        "score": float(score), # <-- Convert the score to a standard float
                        "features": {k: v for k, v in features.items() if k not in ['ticker', 'date']}
                    }
                    
                    save_score_data(score_data)

                except ValueError as e:
                    # This is expected for non-trading days, so we can ignore it.
                    # print(f"Skipping {target_date_str} for {ticker}: {e}")
                    pass
                except Exception as e:
                    print(f"❌ Error processing {ticker} on {target_date_str}: {e}")
            
            print(f"✅ Successfully completed backfill for {ticker}.")
            # A small delay to avoid hitting API rate limits if any
            time.sleep(2)

        except Exception as e:
            print(f"❌ A major error occurred while processing {ticker}: {e}")

    print("\n✅✅ Historical data backfill finished! ✅✅")


if __name__ == "__main__":
    run_historical_backfill()