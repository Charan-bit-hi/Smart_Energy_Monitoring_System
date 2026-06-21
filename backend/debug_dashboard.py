import sys, os, traceback
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db import get_db
from datetime import datetime, timedelta

try:
    db = get_db()
    meters = list(db["meters"].find({}))
    
    # Simulate full dashboard computation step by step
    current_load_kw = 0.0
    total_energy_kwh = 0.0
    meter_details = []
    
    for meter in meters:
        print(f"\n--- Meter: {meter['meterId']} ---")
        latest = db["readings"].find_one(
            {"meterId": meter["meterId"]},
            sort=[("timestamp", -1)]
        )
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
        print(f"Load: {meter_load}, Energy: {meter_energy}")

    # Test site breakdown
    print("\n--- Site breakdown ---")
    sites = list(db["sites"].find({}))
    site_breakdown = []
    for s in sites:
        print(f"Site: {s['siteId']}")
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
        print(f"  Load: {s_load}, Energy: {s_energy}")

    print("\n--- SUCCESS: Dashboard data constructed correctly ---")
    print("Total Load:", current_load_kw)
    print("Total Energy:", total_energy_kwh)

except Exception as e:
    print("\n--- EXCEPTION ---")
    traceback.print_exc()
