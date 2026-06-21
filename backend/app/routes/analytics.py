from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from datetime import datetime, timedelta
import dateutil.parser

from app.auth import get_current_user, UserSession
from app.db import get_db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/peak-usage")
def get_peak_usage(
    siteId: Optional[str] = None,
    days: int = 7,
    current_user: UserSession = Depends(get_current_user)
):
    """
    Returns the average and maximum power load aggregated by hour of the day
    (0-23) over the specified trailing number of days.
    """
    db = get_db()
    
    # Resolve meters
    meter_filter = {}
    if siteId:
        meter_filter["siteId"] = siteId
    meters = list(db["meters"].find(meter_filter))
    meter_ids = [m["meterId"] for m in meters]
    
    start_time = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    
    pipeline = [
        {"$match": {
            "meterId": {"$in": meter_ids},
            "timestamp": {"$gte": start_time}
        }},
        {"$project": {
            # Extract the hour part from the ISO timestamp string "YYYY-MM-DDTHH:mm:ssZ"
            # It starts at index 11 (0-indexed) and is 2 characters long
            "hour": {"$substr": ["$timestamp", 11, 2]},
            "powerKw": 1
        }},
        {"$group": {
            "_id": "$hour",
            "avgLoadKw": {"$avg": "$powerKw"},
            "maxLoadKw": {"$max": "$powerKw"},
            "readingsCount": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    cursor = db["readings"].aggregate(pipeline)
    
    # Create slots for all 24 hours
    hourly_stats = {f"{h:02d}": {"hour": f"{h:02d}:00", "avgLoadKw": 0.0, "maxLoadKw": 0.0, "count": 0} for h in range(24)}
    
    for r in cursor:
        hour_key = r["_id"]
        if hour_key in hourly_stats:
            hourly_stats[hour_key]["avgLoadKw"] = round(r["avgLoadKw"], 2)
            hourly_stats[hour_key]["maxLoadKw"] = round(r["maxLoadKw"], 2)
            hourly_stats[hour_key]["count"] = r["readingsCount"]
            
    return list(hourly_stats.values())

@router.get("/top-consumers")
def get_top_consumers(
    siteId: Optional[str] = None,
    limit: int = 5,
    days: int = 7,
    current_user: UserSession = Depends(get_current_user)
):
    """
    Returns the top consuming meters based on their energy consumption (kWh)
    in the trailing number of days.
    """
    db = get_db()
    
    # 1. Resolve meters
    meter_filter = {}
    if siteId:
        meter_filter["siteId"] = siteId
    meters = list(db["meters"].find(meter_filter))
    if not meters:
        return []
        
    start_time = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    
    consumers = []
    
    # For each meter, compute the energy consumption (difference between max and min energyKwh in range)
    for meter in meters:
        latest = db["readings"].find_one(
            {"meterId": meter["meterId"], "timestamp": {"$gte": start_time}},
            sort=[("timestamp", -1)]
        )
        earliest = db["readings"].find_one(
            {"meterId": meter["meterId"], "timestamp": {"$gte": start_time}},
            sort=[("timestamp", 1)]
        )
        
        consumption = 0.0
        latest_load = 0.0
        
        if latest:
            latest_load = latest["powerKw"]
            if earliest:
                consumption = max(0.0, latest["energyKwh"] - earliest["energyKwh"])
                
        consumers.append({
            "meterId": meter["meterId"],
            "label": meter["label"],
            "serialNumber": meter["serialNumber"],
            "siteId": meter["siteId"],
            "energyConsumedKwh": round(consumption, 2),
            "currentLoadKw": round(latest_load, 2)
        })
        
    # Sort by consumption descending
    consumers.sort(key=lambda x: x["energyConsumedKwh"], reverse=True)
    
    return consumers[:limit]
