# app/main.py
import os 
from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from typing import List, Dict
import pytz

from . import database
from .tasks import run_daily_scoring_job




# Initialize the FastAPI app
app = FastAPI(
    title="Real-Time Explainable Credit Intelligence Platform",
    description="API to serve creditworthiness scores and run daily calculations.",
    version="1.0.0"
)

# --- Scheduler Setup ---
scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(run_daily_scoring_job, 'cron', day_of_week='mon-fri', hour=20, minute=0)
    scheduler.start()
    print("Scheduler started. Daily job scheduled for 8:00 PM IST (Mon-Fri).")

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    print("Scheduler shut down.")


# --- API Endpoints ---
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

# --- UPDATED ENDPOINT ---
@app.get("/scores/{ticker}/{date}", tags=["Scores"], response_model=Dict)
def get_score_for_ticker_on_date(ticker: str, date: str):
    """
    Get the creditworthiness score for a specific ticker on a given date.
    If the date is not a trading day, the score from the most recent previous
    trading day will be returned. The date must be in YYYY-MM-DD format.
    """
    # Call the new, more flexible database function
    score_data = database.get_score_for_date_or_earlier(ticker.upper(), date)
    
    if not score_data:
        # This error will now only happen if there's no data at all before the requested date
        raise HTTPException(
            status_code=404, 
            detail=f"No score found for ticker '{ticker}' on or before '{date}'. "
                   "Ensure the date is within the available data range and in YYYY-MM-DD format."
        )
    return score_data
