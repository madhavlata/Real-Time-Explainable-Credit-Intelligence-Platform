# backfill_historical_data.py (CSV-First Logic)

import pandas as pd
from datetime import datetime, timedelta
import time

# Import only the necessary functions from your app
from app.inference import calculate_creditworthiness_with_explain
from app.database import save_score_data

def run_historical_backfill_from_csv():
    """
    Calculates and stores scores using only the pre-computed data from
    'final training.csv' for the last 2 years. This is the correct and
    efficient way to populate historical data.
    """
    print("🚀 Starting CSV-based historical data backfill.")

    try:
        # 1. Load the pre-computed training data
        print("Loading 'final training.csv'...")
        training_df = pd.read_csv("final training.csv", parse_dates=["date"])
        print(f"Loaded {len(training_df)} rows from CSV.")

        # 2. Define the date range and filter the dataframe
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 2)
        
        df_to_process = training_df[training_df["date"] >= start_date].copy()
        print(f"Processing {len(df_to_process)} rows from the last 2 years.")

        if df_to_process.empty:
            print("⚠️ No data found in 'final training.csv' for the last 2 years. Backfill complete.")
            return

        # 3. Iterate through each row of the filtered dataframe
        for index, row in df_to_process.iterrows():
            try:
                # 4. Extract features directly from the row
                features = row.to_dict()
                
                # Ensure date is a string in the correct format for the database
                features['date'] = features['date'].strftime('%Y-%m-%d')
                
                ticker = features.get("ticker")
                if not ticker:
                    print(f"⚠️ Skipping row {index} due to missing ticker.")
                    continue

                print(f"Processing {ticker} for date {features['date']} from CSV...")

                # 5. Calculate score and explanations using the data from the CSV row
                creditworthiness, probs, shap_metadata = calculate_creditworthiness_with_explain(features, method="weighted")
                
                # 6. Prepare the full data object for storage
                score_data = {
                    "ticker": ticker,
                    "date": features['date'],
                    "creditworthiness": creditworthiness,
                    "risk_probs": probs,
                    "shap_explanations": shap_metadata,
                    "features": {k: v for k, v in features.items() if k not in ['ticker', 'date']}
                }
                
                # 7. Save to DB
                save_score_data(score_data)

            except Exception as e:
                print(f"❌ Error processing row {index} for ticker {features.get('ticker', 'N/A')}: {e}")
        
    except FileNotFoundError:
        print("❌ CRITICAL ERROR: 'final training.csv' not found. Cannot run backfill.")
        return
    except Exception as e:
        print(f"❌ A major error occurred during the backfill process: {e}")

    print("\n✅✅ CSV-based historical data backfill finished! ✅✅")


if __name__ == "__main__":
    run_historical_backfill_from_csv()
