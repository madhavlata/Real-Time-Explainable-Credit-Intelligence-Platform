# app/database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# Establish a connection to the database
client = MongoClient(MONGO_URI)
db = client.credit_intelligence # Use a database named 'credit_intelligence'
scores_collection = db.scores   # Use a collection named 'scores'

def save_score_data(data: Dict):
    """Inserts a single score document into the collection."""
    if isinstance(data['date'], str):
        data['date'] = datetime.strptime(data['date'], '%Y-%m-%d')
    scores_collection.insert_one(data)
    print(f"✅ Successfully saved score for {data['ticker']} on {data['date'].strftime('%Y-%m-%d')}")

def get_scores_by_ticker(ticker: str) -> List[Dict]:
    """Fetches all scores for a given ticker, sorted by date."""
    cursor = scores_collection.find({"ticker": ticker}).sort("date", -1)
    results = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        doc['date'] = doc['date'].strftime('%Y-%m-%d')
        results.append(doc)
    return results

def get_latest_scores() -> List[Dict]:
    """Fetches the most recent score for each monitored ticker."""
    pipeline = [
        {"$sort": {"date": -1}},
        {"$group": {
            "_id": "$ticker",
            "latest_score": {"$first": "$score"},
            "date": {"$first": "$date"},
            "features": {"$first": "$features"}
        }},
        {"$project": {
            "_id": 0,
            "ticker": "$_id",
            "score": "$latest_score",
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
            "features": 1
        }}
    ]
    cursor = scores_collection.aggregate(pipeline)
    return list(cursor)

# --- NEW AND IMPROVED FUNCTION ---
def get_score_for_date_or_earlier(ticker: str, date_str: str) -> Optional[Dict]:
    """
    Fetches the score for a given ticker on a specific date.
    If no score exists for that date, it finds the most recent score on or before it.
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Query for documents where the date is less than or equal to ($lte) the target date.
        # Sort by date descending (-1) and limit to 1 to get the most recent one.
        cursor = scores_collection.find({
            "ticker": ticker,
            "date": {"$lte": target_date}
        }).sort("date", -1).limit(1)
        
        # next() gets the first item from the cursor, or None if it's empty
        doc = next(cursor, None)
        
        if doc:
            doc['_id'] = str(doc['_id'])
            doc['date'] = doc['date'].strftime('%Y-%m-%d')
            return doc
            
        return None
    except (ValueError, StopIteration):
        # Handles bad date formats or an empty database cursor
        return None
