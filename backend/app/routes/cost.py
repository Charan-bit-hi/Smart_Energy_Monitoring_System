from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict
from datetime import datetime
import dateutil.parser

from app.auth import require_roles, UserSession
from app.db import get_db

router = APIRouter(prefix="/api/cost", tags=["Cost & Billing"])

@router.get("/calculate")
def calculate_cost(
    startTime: str,
    endTime: str,
    siteId: Optional[str] = None,
    meterId: Optional[str] = None,
    current_user: UserSession = Depends(require_roles(["Admin", "Manager"]))
):
    db = get_db()
    
    try:
        start_dt = dateutil.parser.isoparse(startTime)
        end_dt = dateutil.parser.isoparse(endTime)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ISO datetime format for startTime or endTime."
        )
        
    # 1. Resolve meters
    meter_query = {}
    if meterId:
        meter_query["meterId"] = meterId
    elif siteId:
        meter_query["siteId"] = siteId
        
    meters = list(db["meters"].find(meter_query))
    if not meters:
        return {
            "totalEnergyKwh": 0.0,
            "totalCostUsd": 0.0,
            "metersCount": 0,
            "details": []
        }
        
    meter_ids = [m["meterId"] for m in meters]
    
    # 2. Get Tariffs
    tariffs = list(db["tariffs"].find({"organizationId": current_user.organizationId}))
    # Find standard tariff and peak tariff
    standard_rate = 0.12 # fallback
    peak_rate = 0.18     # fallback
    
    for t in tariffs:
        if "peak" in t["name"].lower():
            peak_rate = t["ratePerKwh"]
        else:
            standard_rate = t["ratePerKwh"]
            
    # 3. Process readings for each meter
    total_energy_kwh = 0.0
    total_cost_usd = 0.0
    meter_details = []
    
    for meter in meters:
        # Find readings in this time range sorted by timestamp asc
        readings = list(db["readings"].find({
            "meterId": meter["meterId"],
            "timestamp": {
                "$gte": startTime,
                "$lte": endTime
            }
        }).sort("timestamp", 1))
        
        meter_energy = 0.0
        meter_cost = 0.0
        
        if len(readings) >= 2:
            # We calculate intervals
            for i in range(1, len(readings)):
                prev = readings[i-1]
                curr = readings[i]
                
                energy_diff = max(0.0, curr["energyKwh"] - prev["energyKwh"])
                if energy_diff <= 0.0:
                    continue
                    
                # Determine rate based on timestamp hour (e.g., peak is 14:00 to 18:00)
                try:
                    curr_dt = dateutil.parser.isoparse(curr["timestamp"])
                    # Check if hour is between 14 (2 PM) and 18 (6 PM) local/UTC depending on tz
                    # We'll check hour in UTC for simplicity
                    is_peak = 14 <= curr_dt.hour < 18
                except Exception:
                    is_peak = False
                    
                rate = peak_rate if is_peak else standard_rate
                cost_diff = energy_diff * rate
                
                meter_energy += energy_diff
                meter_cost += cost_diff
                
            total_energy_kwh += meter_energy
            total_cost_usd += meter_cost
            
        elif len(readings) == 1:
            # Fallback if only 1 reading: compare to the very earliest reading available in DB
            earliest = db["readings"].find_one({"meterId": meter["meterId"]}, sort=[("timestamp", 1)])
            if earliest and earliest["readingId"] != readings[0]["readingId"]:
                energy_diff = max(0.0, readings[0]["energyKwh"] - earliest["energyKwh"])
                rate = standard_rate
                meter_energy = energy_diff
                meter_cost = energy_diff * rate
                total_energy_kwh += meter_energy
                total_cost_usd += meter_cost

        meter_details.append({
            "meterId": meter["meterId"],
            "label": meter["label"],
            "serialNumber": meter["serialNumber"],
            "energyKwh": round(meter_energy, 2),
            "costUsd": round(meter_cost, 2)
        })
        
    return {
        "startTime": startTime,
        "endTime": endTime,
        "totalEnergyKwh": round(total_energy_kwh, 2),
        "totalCostUsd": round(total_cost_usd, 2),
        "standardRate": standard_rate,
        "peakRate": peak_rate,
        "metersCount": len(meters),
        "details": meter_details
    }
