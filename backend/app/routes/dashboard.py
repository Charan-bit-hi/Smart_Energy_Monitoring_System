from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
import time
import traceback
from typing import Dict, Any, Optional

from app.auth import get_current_user, UserSession
from app.db import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Simulating Redis cache with in-memory store
CACHE_TTL_SECONDS = 10  # Cache aggregates for 10 seconds to show dynamic caching
cache_store: Dict[str, Dict[str, Any]] = {}

def get_cached_summary(site_id: str = None) -> Any:
    cache_key = f"dashboard_summary_{site_id or 'all'}"
    if cache_key in cache_store:
        entry = cache_store[cache_key]
        if time.time() - entry["timestamp"] < CACHE_TTL_SECONDS:
            print("[CACHE HIT - REDIS SIMULATOR] Returning cached dashboard summary.")
            return entry["data"]
    return None

def set_cached_summary(data: Any, site_id: str = None):
    cache_key = f"dashboard_summary_{site_id or 'all'}"
    cache_store[cache_key] = {
        "timestamp": time.time(),
        "data": data
    }
    print("[CACHE MISS - REDIS SIMULATOR] Calculated and cached new dashboard summary.")

@router.get("/summary")
def get_dashboard_summary(
    siteId: Optional[str] = None,
    current_user: UserSession = Depends(get_current_user)
):
    # Try fetching from cache
    cached_data = get_cached_summary(siteId)
    if cached_data:
        return cached_data

    try:
        return _compute_dashboard_summary(siteId, current_user)
    except Exception as e:
        print("[DASHBOARD ERROR] Exception in get_dashboard_summary:")
        traceback.print_exc()
        raise

def _compute_dashboard_summary(siteId, current_user):
    db = get_db()
    
    # 1. Get Meters Filter
    meter_filter = {}
    if siteId:
        meter_filter["siteId"] = siteId
        
    meters = list(db["meters"].find(meter_filter))
    meter_ids = [m["meterId"] for m in meters]
    
    total_meters = len(meters)
    active_meters = sum(1 for m in meters if m["status"] == "Active")
    faulty_meters = sum(1 for m in meters if m["status"] == "Faulty")
    
    # 2. Calculate Active Alerts Count
    alert_filter = {"acknowledged": False}
    if siteId:
        # Get alerts only for meters belonging to the site
        alert_filter["meterId"] = {"$in": meter_ids}
    active_alerts_count = db["alerts"].count_documents(alert_filter)
    
    # 3. Calculate Current Load (kW) & Total Energy Consumed (kWh)
    # Current load = sum of the latest powerKw reading for each meter
    current_load_kw = 0.0
    total_energy_kwh = 0.0
    
    meter_details = []
    
    for meter in meters:
        # Latest reading for current load
        latest = db["readings"].find_one(
            {"meterId": meter["meterId"]},
            sort=[("timestamp", -1)]
        )
        # Earliest reading for baseline energy
        earliest = db["readings"].find_one(
            {"meterId": meter["meterId"]},
            sort=[("timestamp", 1)]
        )
        
        meter_load = 0.0
        meter_energy = 0.0
        
        if latest:
            meter_load = latest["powerKw"]
            current_load_kw += meter_load
            
            if earliest:
                # Energy consumed is the difference in cumulative energyKwh
                meter_energy = max(0.0, latest["energyKwh"] - earliest["energyKwh"])
                total_energy_kwh += meter_energy
                
        meter_details.append({
            "meterId": meter["meterId"],
            "label": meter["label"],
            "serialNumber": meter["serialNumber"],
            "status": meter["status"],
            "currentLoadKw": round(meter_load, 2),
            "energyConsumedKwh": round(meter_energy, 2),
            "lastActive": latest["timestamp"] if latest else None
        })
        
    # 4. Aggregated hourly usage for chart (last 24 hours)
    # We will aggregate readings by hour
    one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    
    pipeline = [
        {"$match": {
            "meterId": {"$in": meter_ids},
            "timestamp": {"$gte": one_day_ago}
        }},
        {"$project": {
            # Format timestamp to YYYY-MM-DDTHH:00:00Z
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
    
    chart_cursor = db["readings"].aggregate(pipeline)
    chart_data = []
    for c in chart_cursor:
        # Formatting hour back to readable label, e.g. "14:00"
        hour_str = c["_id"].split("T")[1] + ":00"
        chart_data.append({
            "time": hour_str,
            "avgLoadKw": round(c["avgLoadKw"], 2),
            "maxLoadKw": round(c["maxLoadKw"], 2),
        })
        
    # If no chart data (no readings in past 24h), supply mock structure for UI elegance
    if not chart_data:
        for h in range(24):
            time_label = f"{(datetime.utcnow() - timedelta(hours=23-h)).hour:02d}:00"
            chart_data.append({
                "time": time_label,
                "avgLoadKw": 0.0,
                "maxLoadKw": 0.0
            })
            
    # 5. Site Consumption Breakdown (if querying for all sites)
    site_breakdown = []
    if not siteId:
        sites = list(db["sites"].find({}))
        for s in sites:
            s_meters = list(db["meters"].find({"siteId": s["siteId"]}))
            s_meter_ids = [sm["meterId"] for sm in s_meters]
            
            s_energy = 0.0
            s_load = 0.0
            
            for smid in s_meter_ids:
                s_latest = db["readings"].find_one({"meterId": smid}, sort=[("timestamp", -1)])
                s_earliest = db["readings"].find_one({"meterId": smid}, sort=[("timestamp", 1)])
                if s_latest:
                    s_load += s_latest["powerKw"]
                    if s_earliest:
                        s_energy += max(0.0, s_latest["energyKwh"] - s_earliest["energyKwh"])
            
            site_breakdown.append({
                "siteId": s["siteId"],
                "name": s["name"],
                "activeMeters": len([sm for sm in s_meters if sm["status"] == "Active"]),
                "currentLoadKw": round(s_load, 2),
                "energyConsumedKwh": round(s_energy, 2)
            })

    result = {
        "totalMeters": total_meters,
        "activeMeters": active_meters,
        "faultyMeters": faulty_meters,
        "activeAlertsCount": active_alerts_count,
        "currentLoadKw": round(current_load_kw, 2),
        "totalEnergyKwh": round(total_energy_kwh, 2),
        "meterDetails": meter_details,
        "hourlyUsage": chart_data,
        "siteBreakdown": site_breakdown
    }
    
    # Save in cache
    set_cached_summary(result, siteId)
    
    return result
