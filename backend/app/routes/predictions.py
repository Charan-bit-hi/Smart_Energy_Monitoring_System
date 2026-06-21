from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime

from app.auth import get_current_user, UserSession
from app.db import get_db
from app.ml.forecaster import train_and_forecast

router = APIRouter(prefix="/api/predictions", tags=["ML Predictions"])

@router.get("/{meter_id}")
def get_predictions(
    meter_id: str,
    hours: int = 24,
    current_user: UserSession = Depends(get_current_user)
):
    db = get_db()
    
    # 1. Verify Meter Exists
    meter = db["meters"].find_one({"meterId": meter_id})
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter '{meter_id}' not registered."
        )
        
    # 2. Get Historical Readings
    # Fetch trailing 100 readings sorted by timestamp asc (older first, which ML models expect)
    readings = list(db["readings"].find({"meterId": meter_id}).sort("timestamp", 1).limit(200))
    
    # 3. Train & Forecast
    forecast_results, confidence_score, model_info = train_and_forecast(readings, forecast_hours=hours)
    
    # 4. Save/Update Predictions in DB (upsert for this meter)
    now = datetime.utcnow().isoformat() + "Z"
    prediction_doc = {
        "meterId": meter_id,
        "predictions": forecast_results,
        "confidenceScore": confidence_score,
        "modelUsed": model_info,
        "modelRunAt": now
    }
    
    db["predictions"].replace_one(
        {"meterId": meter_id},
        prediction_doc,
        upsert=True
    )
    
    return {
        "meterId": meter_id,
        "modelUsed": model_info,
        "confidenceScore": confidence_score,
        "modelRunAt": now,
        "predictions": forecast_results
    }
