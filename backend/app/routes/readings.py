from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.auth import get_current_user, UserSession
from app.db import get_db

router = APIRouter(prefix="/api/readings", tags=["Readings"])

class ReadingIngest(BaseModel):
    meterId: str
    voltage: float
    current: float
    powerKw: float
    energyKwh: float
    timestamp: Optional[str] = None

class ReadingResponse(BaseModel):
    readingId: str
    meterId: str
    voltage: float
    current: float
    powerKw: float
    energyKwh: float
    timestamp: str

def run_alert_engine(db, reading: ReadingIngest):
    """
    Synchronous Alert Engine:
    Evaluates readings against basic thresholds and logs alerts when breached.
    """
    alerts_triggered = []
    
    # Rules
    # 1. Over-Voltage (> 250V) or Under-Voltage (< 200V)
    if reading.voltage > 250.0:
        alerts_triggered.append({
            "type": "Threshold",
            "threshold": 250.0,
            "actual": reading.voltage,
            "severity": "Warning",
            "message": f"Overvoltage detected: {reading.voltage}V (threshold: 250V)"
        })
    elif reading.voltage < 200.0:
        alerts_triggered.append({
            "type": "Threshold",
            "threshold": 200.0,
            "actual": reading.voltage,
            "severity": "Critical",
            "message": f"Undervoltage detected: {reading.voltage}V (threshold: 200V)"
        })
        
    # 2. Overcurrent (> 200A)
    if reading.current > 200.0:
        alerts_triggered.append({
            "type": "Threshold",
            "threshold": 200.0,
            "actual": reading.current,
            "severity": "Warning",
            "message": f"Overcurrent detected: {reading.current}A (threshold: 200A)"
        })
        
    # 3. High Power Load (> 50 kW)
    if reading.powerKw > 50.0:
        alerts_triggered.append({
            "type": "Threshold",
            "threshold": 50.0,
            "actual": reading.powerKw,
            "severity": "Critical",
            "message": f"High Load breach: {reading.powerKw}kW (threshold: 50kW)"
        })
        
    # Write alerts to database and print mock notifications
    for alert in alerts_triggered:
        import uuid
        alert_doc = {
            "alertId": f"alt_{uuid.uuid4().hex[:12]}",
            "meterId": reading.meterId,
            "alertType": alert["type"],
            "thresholdValue": alert["threshold"],
            "actualValue": alert["actual"],
            "severity": alert["severity"],
            "message": alert["message"],
            "triggeredAt": reading.timestamp or datetime.utcnow().isoformat() + "Z",
            "acknowledged": False
        }
        db["alerts"].insert_one(alert_doc)
        print(f"[ALERT - NOTIFICATION STUB] Alert on Meter '{reading.meterId}': {alert['message']} ({alert['severity']})")

@router.post("", status_code=status.HTTP_201_CREATED)
def ingest_reading(
    reading: ReadingIngest,
    x_meter_token: Optional[str] = Header(None, alias="X-Meter-Token"),
    device_token_query: Optional[str] = None
):
    db = get_db()
    
    # 1. Authenticate Meter
    meter = db["meters"].find_one({"meterId": reading.meterId})
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter '{reading.meterId}' not registered."
        )
        
    # Verify token (either in header X-Meter-Token or query parameter)
    provided_token = x_meter_token or device_token_query or reading.meterId # fallback for simulation convenience
    if provided_token != meter.get("deviceToken") and provided_token != reading.meterId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid meter authentication token."
        )
        
    # If the meter is marked as Faulty or Inactive, set it back to Active when receiving data
    if meter["status"] != "Active":
        db["meters"].update_one({"meterId": reading.meterId}, {"$set": {"status": "Active"}})

    # 2. Prepare Timestamp
    if not reading.timestamp:
        reading.timestamp = datetime.utcnow().isoformat() + "Z"
    elif not reading.timestamp.endswith("Z"):
        # Make sure timestamp format is normalized
        reading.timestamp = reading.timestamp + "Z"

    # 3. Insert Reading
    import uuid
    reading_id = f"rdg_{uuid.uuid4().hex[:12]}"
    
    reading_doc = {
        "readingId": reading_id,
        "meterId": reading.meterId,
        "voltage": reading.voltage,
        "current": reading.current,
        "powerKw": reading.powerKw,
        "energyKwh": reading.energyKwh,
        "timestamp": reading.timestamp
    }
    
    db["readings"].insert_one(reading_doc)
    
    # 4. Trigger Alert Evaluation
    run_alert_engine(db, reading)
    
    return {"status": "success", "readingId": reading_id}

@router.get("/{meter_id}", response_model=List[ReadingResponse])
def get_historical_readings(
    meter_id: str,
    limit: int = 100,
    current_user: UserSession = Depends(get_current_user)
):
    db = get_db()
    
    # Verify meter exists
    meter = db["meters"].find_one({"meterId": meter_id})
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter '{meter_id}' not found."
        )
        
    # Find historical readings sorted by timestamp desc
    cursor = db["readings"].find({"meterId": meter_id}).sort("timestamp", -1).limit(limit)
    
    readings = []
    for r in cursor:
        readings.append(ReadingResponse(
            readingId=r["readingId"],
            meterId=r["meterId"],
            voltage=r["voltage"],
            current=r["current"],
            powerKw=r["powerKw"],
            energyKwh=r["energyKwh"],
            timestamp=r["timestamp"]
        ))
    return readings
