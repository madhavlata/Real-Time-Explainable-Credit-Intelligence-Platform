# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from typing import List, Dict, Any
import pytz

from . import database
from .tasks import run_daily_scoring_job
# --- UPDATED IMPORTS ---
from .inference import get_ticker_features, calculate_creditworthiness_with_explain

# Initialize the FastAPI app
app = FastAPI(
    title="Real-Time Explainable Credit Intelligence Platform",
    description="API to serve creditworthiness scores and run daily calculations.",
    version="1.0.0"
)

# --- CORS MIDDLEWARE SETUP ---
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://real-time-explainable-credit-intell.vercel.app",
    # "https://your-deployed-frontend-url.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SCHEDULER SETUP ---
scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Kolkata"))

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(run_daily_scoring_job, 'cron', day_of_week='mon-fri', hour=20, minute=0)
    scheduler.start()
    print("Scheduler started. Daily job scheduled for 8:00 PM IST (Mon-Fri).")

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    print("Scheduler shut down.")


# --- API ENDPOINTS ---
@app.get("/", tags=["Status"])
def read_root():
    """Root endpoint to check if the API is running."""
    return {"status": "Credit Intelligence API is running"}

# Note: The response_model for these endpoints will now be a list of the new, complex objects
@app.get("/scores/latest", tags=["Scores"], response_model=List[Dict[str, Any]])
def get_latest_scores():
    """Get the most recent creditworthiness score for all monitored tickers."""
    scores = database.get_latest_scores()
    if not scores:
        raise HTTPException(status_code=404, detail="No scores found in the database.")
    return scores

@app.get("/scores/{ticker}", tags=["Scores"], response_model=List[Dict[str, Any]])
def get_scores_for_ticker(ticker: str):
    """Get the historical creditworthiness scores for a specific ticker."""
    scores = database.get_scores_by_ticker(ticker.upper())
    if not scores:
        raise HTTPException(status_code=404, detail=f"No scores found for ticker '{ticker}'.")
    return scores

# --- HEAVILY UPDATED ENDPOINT WITH NEW INFERENCE LOGIC ---
@app.get("/scores/{ticker}/{date}", tags=["Scores"], response_model=Dict[str, Any])
def get_score_for_ticker_on_date(ticker: str, date: str):
    """
    Get the creditworthiness score and explanation for a specific ticker and date.
    If data is not in the DB, it's calculated on-the-fly.
    """
    ticker_upper = ticker.upper()
    score_data = database.get_score_for_date_or_earlier(ticker_upper, date)
    
    if score_data:
        print(f"Found cached data for {ticker_upper} in DB.")
        return score_data

    print(f"Data for {ticker_upper} not found in DB. Calculating on-the-fly...")
    try:
        # 1. Get features using the new logic (which includes sentiment)
        features = get_ticker_features(ticker_upper, date)
        features["ticker"] = ticker_upper

        # 2. Calculate score and explanations
        creditworthiness, probs, shap_metadata = calculate_creditworthiness_with_explain(features, method="weighted")

        # 3. Prepare the full data object
        new_score_data = {
            "ticker": ticker_upper,
            "date": features['date'],
            "creditworthiness": creditworthiness,
            "risk_probs": probs,
            "shap_explanations": shap_metadata,
            "features": {k: v for k, v in features.items() if k not in ['ticker', 'date']}
        }

        # 4. Save to DB and return
        database.save_score_data(new_score_data.copy())
        return new_score_data

    except ValueError as e:
        print(f"Error calculating on-the-fly for {ticker_upper}: {e}")
        raise HTTPException(
            status_code=404, 
            detail=f"Could not fetch or calculate data for ticker '{ticker_upper}'. It may be an invalid symbol."
        )
    except Exception as e:
        print(f"A general error occurred during on-the-fly calculation for {ticker_upper}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred while calculating the score for '{ticker_upper}'."
        )
