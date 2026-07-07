from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.device import Device
from app.models.device_correction import DeviceCorrection

router = APIRouter()

class CorrectionCreate(BaseModel):
    mac_address: str
    field_name: str
    new_value: str
    old_value: Optional[str] = ""
    reason: Optional[str] = ""

@router.post("/correct")
def create_correction(body: CorrectionCreate, db: Session = Depends(get_db)):
    mac = body.mac_address.upper()
    
    device = db.query(Device).filter(Device.mac_address == mac).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    old_value = body.old_value
    if not old_value:
        if body.field_name == "vendor":
            old_value = device.vendor or ""
        elif body.field_name == "device_type":
            old_value = device.device_type or ""
        elif body.field_name == "hostname":
            old_value = device.hostname or ""
        else:
            old_value = ""
    
    if body.field_name == "vendor":
        device.vendor = body.new_value
    elif body.field_name == "device_type":
        device.device_type = body.new_value
    elif body.field_name == "hostname":
        device.hostname = body.new_value
    
    correction = DeviceCorrection(
        mac_address=mac,
        field_name=body.field_name,
        old_value=old_value,
        new_value=body.new_value,
        reason=body.reason,
    )
    db.add(correction)
    db.commit()
    
    return {"status": "ok", "message": f"Updated {body.field_name} for {mac}"}

@router.get("/corrections/{mac_address}")
def get_corrections(mac_address: str, db: Session = Depends(get_db)):
    mac = mac_address.upper()
    corrections = db.query(DeviceCorrection).filter(
        DeviceCorrection.mac_address == mac
    ).order_by(DeviceCorrection.created_at.desc()).all()
    
    return [
        {
            "id": c.id,
            "mac_address": c.mac_address,
            "field_name": c.field_name,
            "old_value": c.old_value,
            "new_value": c.new_value,
            "reason": c.reason,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in corrections
    ]

@router.get("/corrections")
def list_all_corrections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    corrections = db.query(DeviceCorrection).order_by(
        DeviceCorrection.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": c.id,
            "mac_address": c.mac_address,
            "field_name": c.field_name,
            "old_value": c.old_value,
            "new_value": c.new_value,
            "reason": c.reason,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in corrections
    ]

@router.get("/learned-rules")
def get_learned_rules(db: Session = Depends(get_db)):
    corrections = db.query(DeviceCorrection).all()
    
    rules = {}
    for c in corrections:
        key = c.mac_address[:8]
        if key not in rules:
            rules[key] = {"mac_prefix": key, "corrections": []}
        rules[key]["corrections"].append({
            "field": c.field_name,
            "value": c.new_value,
        })
    
    return list(rules.values())

def get_learned_vendor(mac_prefix: str, db: Session) -> str:
    correction = db.query(DeviceCorrection).filter(
        DeviceCorrection.mac_address.startswith(mac_prefix),
        DeviceCorrection.field_name == "vendor"
    ).order_by(DeviceCorrection.created_at.desc()).first()
    return correction.new_value if correction else None

def get_learned_device_type(mac_prefix: str, db: Session) -> str:
    correction = db.query(DeviceCorrection).filter(
        DeviceCorrection.mac_address.startswith(mac_prefix),
        DeviceCorrection.field_name == "device_type"
    ).order_by(DeviceCorrection.created_at.desc()).first()
    return correction.new_value if correction else None
