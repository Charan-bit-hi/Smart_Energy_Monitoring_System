from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.auth import get_current_user, require_roles, UserSession
from app.db import get_db

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

class AlertResponse(BaseModel):
    alertId: str
    meterId: str
    alertType: str
    thresholdValue: float
    actualValue: float
    severity: str
    message: str
    triggeredAt: str
    acknowledged: bool
    acknowledgedBy: Optional[str] = None
    acknowledgedAt: Optional[str] = None

@router.get("", response_model=List[AlertResponse])
def list_alerts(
    acknowledged: Optional[bool] = None,
    severity: Optional[str] = None,
    meterId: Optional[str] = None,
    current_user: UserSession = Depends(get_current_user)
):
    db = get_db()
    query = {}
    
    if acknowledged is not None:
        query["acknowledged"] = acknowledged
    if severity:
        query["severity"] = severity
    if meterId:
        query["meterId"] = meterId
        
    cursor = db["alerts"].find(query).sort("triggeredAt", -1).limit(100)
    
    alerts = []
    for a in cursor:
        alerts.append(AlertResponse(
            alertId=a["alertId"],
            meterId=a["meterId"],
            alertType=a["alertType"],
            thresholdValue=a["thresholdValue"],
            actualValue=a["actualValue"],
            severity=a["severity"],
            message=a.get("message", ""),
            triggeredAt=a["triggeredAt"],
            acknowledged=a["acknowledged"],
            acknowledgedBy=a.get("acknowledgedBy"),
            acknowledgedAt=a.get("acknowledgedAt")
        ))
    return alerts

@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: str,
    current_user: UserSession = Depends(require_roles(["Admin", "Manager", "Engineer"]))
):
    db = get_db()
    alert = db["alerts"].find_one({"alertId": alert_id})
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found."
        )
        
    if alert["acknowledged"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already acknowledged."
        )
        
    now = datetime.utcnow().isoformat() + "Z"
    db["alerts"].update_one(
        {"alertId": alert_id},
        {"$set": {
            "acknowledged": True,
            "acknowledgedBy": current_user.email,
            "acknowledgedAt": now
        }}
    )
    
    updated_alert = db["alerts"].find_one({"alertId": alert_id})
    
    return AlertResponse(
        alertId=updated_alert["alertId"],
        meterId=updated_alert["meterId"],
        alertType=updated_alert["alertType"],
        thresholdValue=updated_alert["thresholdValue"],
        actualValue=updated_alert["actualValue"],
        severity=updated_alert["severity"],
        message=updated_alert.get("message", ""),
        triggeredAt=updated_alert["triggeredAt"],
        acknowledged=updated_alert["acknowledged"],
        acknowledgedBy=updated_alert["acknowledgedBy"],
        acknowledgedAt=updated_alert["acknowledgedAt"]
    )
