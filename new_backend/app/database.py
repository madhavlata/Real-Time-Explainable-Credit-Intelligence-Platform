# app/database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.credit_intelligence_new
scores_collection = db.scores

def save_score_data(data: Dict):
    """Inserts a single score document into the collection."""
    if isinstance(data['date'], str):
        data['date'] = datetime.strptime(data['date'], '%Y-%m-%d')
    
    # Check if a document for this ticker and date already exists
    existing_doc = scores_collection.find_one({
        "ticker": data["ticker"],
        "date": data["date"]
    })
    
    if not existing_doc:
        scores_collection.insert_one(data)
        print(f"✅ Successfully saved score for {data['ticker']} on {data['date'].strftime('%Y-%m-%d')}")
    else:
        print(f"ℹ️ Score for {data['ticker']} on {data['date'].strftime('%Y-%m-%d')} already exists. Skipping.")


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
            # --- CHANGE: Use 'creditworthiness' instead of 'score' ---
            "latest_creditworthiness": {"$first": "$creditworthiness"},
            "date": {"$first": "$date"},
            "features": {"$first": "$features"}
        }},
        {"$project": {
            "_id": 0,
            "ticker": "$_id",
            # --- CHANGE: Rename the output field ---
            "creditworthiness": "$latest_creditworthiness",
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
            "features": 1
        }}
    ]
    cursor = scores_collection.aggregate(pipeline)
    return list(cursor)

def get_score_for_date_or_earlier(ticker: str, date_str: str) -> Optional[Dict]:
    """
    Fetches the score for a given ticker on a specific date.
    If no score exists for that date, it finds the most recent score on or before it.
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        cursor = scores_collection.find({
            "ticker": ticker,
            "date": {"$lte": target_date}
        }).sort("date", -1).limit(1)
        
        doc = next(cursor, None)
        
        if doc:
            doc['_id'] = str(doc['_id'])
            doc['date'] = doc['date'].strftime('%Y-%m-%d')
            return doc
            
        return None
    except (ValueError, StopIteration):
        return None
