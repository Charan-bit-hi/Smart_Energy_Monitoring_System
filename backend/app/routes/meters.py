from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.auth import get_current_user, require_roles, UserSession
from app.db import get_db

router = APIRouter(prefix="/api/meters", tags=["Meters"])

class MeterCreate(BaseModel):
    siteId: str
    serialNumber: str
    label: str
    status: str = Field(default="Active", description="Active, Inactive, Faulty")

class MeterUpdate(BaseModel):
    siteId: Optional[str] = None
    label: Optional[str] = None
    status: Optional[str] = None

class MeterResponse(BaseModel):
    meterId: str
    siteId: str
    serialNumber: str
    label: str
    status: str
    registeredAt: str
    deviceToken: str

@router.get("", response_model=List[MeterResponse])
def list_meters(
    siteId: Optional[str] = None,
    current_user: UserSession = Depends(get_current_user)
):
    db = get_db()
    query = {}
    
    # If siteId is specified, filter by it
    if siteId:
        query["siteId"] = siteId
        
    # Get meters from database
    meters_cursor = db["meters"].find(query)
    meters = []
    for m in meters_cursor:
        meters.append(MeterResponse(
            meterId=m["meterId"],
            siteId=m["siteId"],
            serialNumber=m["serialNumber"],
            label=m["label"],
            status=m["status"],
            registeredAt=m.get("registeredAt", datetime.utcnow().isoformat()),
            deviceToken=m.get("deviceToken", "")
        ))
    return meters

@router.post("", response_model=MeterResponse, status_code=status.HTTP_201_CREATED)
def create_meter(
    meter_in: MeterCreate,
    current_user: UserSession = Depends(require_roles(["Admin", "Manager"]))
):
    db = get_db()
    
    # Check if serial number already exists
    existing = db["meters"].find_one({"serialNumber": meter_in.serialNumber})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Meter with serial number '{meter_in.serialNumber}' already exists."
        )
        
    # Verify site exists
    site = db["sites"].find_one({"siteId": meter_in.siteId})
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site with siteId '{meter_in.siteId}' not found."
        )

    # Generate meterId and deviceToken
    meter_id = f"mtr_{uuid.uuid4().hex[:12]}"
    device_token = f"token_{uuid.uuid4().hex[:16]}"
    
    new_meter = {
        "meterId": meter_id,
        "siteId": meter_in.siteId,
        "serialNumber": meter_in.serialNumber,
        "label": meter_in.label,
        "status": meter_in.status,
        "registeredAt": datetime.utcnow().isoformat() + "Z",
        "deviceToken": device_token
    }
    
    db["meters"].insert_one(new_meter)
    
    return MeterResponse(
        meterId=new_meter["meterId"],
        siteId=new_meter["siteId"],
        serialNumber=new_meter["serialNumber"],
        label=new_meter["label"],
        status=new_meter["status"],
        registeredAt=new_meter["registeredAt"],
        deviceToken=new_meter["deviceToken"]
    )

@router.get("/{meter_id}", response_model=MeterResponse)
def get_meter(
    meter_id: str,
    current_user: UserSession = Depends(get_current_user)
):
    db = get_db()
    meter = db["meters"].find_one({"meterId": meter_id})
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter '{meter_id}' not found."
        )
    return MeterResponse(
        meterId=meter["meterId"],
        siteId=meter["siteId"],
        serialNumber=meter["serialNumber"],
        label=meter["label"],
        status=meter["status"],
        registeredAt=meter.get("registeredAt", ""),
        deviceToken=meter.get("deviceToken", "")
    )

@router.put("/{meter_id}", response_model=MeterResponse)
def update_meter(
    meter_id: str,
    meter_in: MeterUpdate,
    current_user: UserSession = Depends(require_roles(["Admin"]))
):
    db = get_db()
    meter = db["meters"].find_one({"meterId": meter_id})
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter '{meter_id}' not found."
        )
        
    update_data = {k: v for k, v in meter_in.dict(exclude_unset=True).items()}
    
    if "siteId" in update_data:
        site = db["sites"].find_one({"siteId": update_data["siteId"]})
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Site with siteId '{update_data['siteId']}' not found."
            )
            
    if update_data:
        db["meters"].update_one({"meterId": meter_id}, {"$set": update_data})
        meter = db["meters"].find_one({"meterId": meter_id})
        
    return MeterResponse(
        meterId=meter["meterId"],
        siteId=meter["siteId"],
        serialNumber=meter["serialNumber"],
        label=meter["label"],
        status=meter["status"],
        registeredAt=meter.get("registeredAt", ""),
        deviceToken=meter.get("deviceToken", "")
    )

@router.delete("/{meter_id}")
def delete_meter(
    meter_id: str,
    current_user: UserSession = Depends(require_roles(["Admin"]))
):
    db = get_db()
    meter = db["meters"].find_one({"meterId": meter_id})
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter '{meter_id}' not found."
        )
    # Delete meter and associated readings/alerts
    db["meters"].delete_one({"meterId": meter_id})
    db["readings"].delete_many({"meterId": meter_id})
    db["alerts"].delete_many({"meterId": meter_id})
    
    return {"message": f"Meter '{meter_id}' and all its historical readings/alerts have been deleted."}
