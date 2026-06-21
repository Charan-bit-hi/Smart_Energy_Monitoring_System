import sys
import os

# Add current path to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.db import get_db
from datetime import datetime, timedelta

def run_test():
    db = get_db()
    meter_ids = [m["meterId"] for m in db["meters"].find()]
    one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    
    pipeline = [
        {"$match": {
            "meterId": {"$in": meter_ids},
            "timestamp": {"$gte": one_day_ago}
        }},
        {"$project": {
            "hour": {"$substr": ["$timestamp", 0, 13]},
            "powerKw": 1,
            "energyKwh": 1
        }},
        {"$group": {
            "_id": "$hour",
            "avgLoadKw": {"$avg": "$powerKw"},
            "maxLoadKw": {"$max": "$powerKw"},
            "readingsCount": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    print("Running aggregation pipeline...")
    chart_cursor = list(db["readings"].aggregate(pipeline))
    print(f"Aggregation returned {len(chart_cursor)} rows.")
    
    for c in chart_cursor:
        print(f"Row: {c}")
        # Try formatting
        hour_str = c["_id"].split("T")[1] + ":00"
        print(f"Formatted hour: {hour_str}")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        import traceback
        traceback.print_exc()
