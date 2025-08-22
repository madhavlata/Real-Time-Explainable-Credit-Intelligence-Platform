# app/main.py
from fastapi import FastAPI, HTTPException
# --- NEW IMPORT ---
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from typing import List, Dict
import pytz

from . import database
from .tasks import run_daily_scoring_job
from .inference import get_ticker_features, calculate_creditworthiness

# Initialize the FastAPI app
app = FastAPI(
    title="Real-Time Explainable Credit Intelligence Platform",
    description="API to serve creditworthiness scores and run daily calculations.",
    version="1.0.0"
)

# --- CORS MIDDLEWARE SETUP ---
# Define the list of allowed origins (your frontend URLs)
origins = [
    "http://localhost:3000",      # Your local development frontend
    "http://localhost:5173",      # Vite's default local dev port
    "https://real-time-explainable-credit-intell.vercel.app",
    # "https://your-deployed-frontend-url.com", # Add your deployed frontend URL here
]

# Add the CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # List of origins that are allowed to make requests
    allow_credentials=True,       # Allow cookies to be included in requests
    allow_methods=["*"],          # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],          # Allow all headers
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

@app.get("/scores/latest", tags=["Scores"], response_model=List[Dict])
def get_latest_scores():
    """Get the most recent creditworthiness score for all monitored tickers."""
    scores = database.get_latest_scores()
    if not scores:
        raise HTTPException(status_code=404, detail="No scores found in the database.")
    return scores

@app.get("/scores/{ticker}", tags=["Scores"], response_model=List[Dict])
def get_scores_for_ticker(ticker: str):
    """Get the historical creditworthiness scores for a specific ticker."""
    scores = database.get_scores_by_ticker(ticker.upper())
    if not scores:
        raise HTTPException(status_code=404, detail=f"No scores found for ticker '{ticker}'.")
    return scores

@app.get("/scores/{ticker}/{date}", tags=["Scores"], response_model=Dict)
def get_score_for_ticker_on_date(ticker: str, date: str):
    """
    Get the creditworthiness score for a specific ticker on a given date.
    If the date is not a trading day, the score from the most recent previous
    trading day will be returned.
    If the ticker is not in the database, it will be calculated on-the-fly,
    saved, and then returned.
    """
    ticker_upper = ticker.upper()
    score_data = database.get_score_for_date_or_earlier(ticker_upper, date)
    
    if score_data:
        print(f"Found cached data for {ticker_upper} in DB.")
        return score_data

    print(f"Data for {ticker_upper} not found in DB. Calculating on-the-fly...")
    try:
        features = get_ticker_features(ticker_upper, date)
        score = calculate_creditworthiness(features, method="weighted")
        new_score_data = {
            "ticker": ticker_upper,
            "date": features['date'],
            "score": float(score),
            "features": {k: v for k, v in features.items() if k not in ['ticker', 'date']}
        }
        database.save_score_data(new_score_data.copy())
        return new_score_data

    except ValueError as e:
        print(f"Error calculating on-the-fly for {ticker_upper}: {e}")
        raise HTTPException(
            status_code=404, 
            detail=f"Could not fetch or calculate data for ticker '{ticker_upper}'. It may be an invalid symbol or have no data for the requested period."
        )
    except Exception as e:
        print(f"A general error occurred during on-the-fly calculation for {ticker_upper}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred while calculating the score for '{ticker_upper}'."
        )
