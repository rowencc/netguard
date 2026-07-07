from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.device import Device
from app.models.alert import Alert
import subprocess
import sys
from pathlib import Path

router = APIRouter()

SCRIPT_DIR = Path(__file__).parent.parent.parent


@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    device_count = db.query(Device).filter(Device.scan_source == "client").count()
    alert_count = db.query(Alert).filter(Alert.acknowledged == False).count()
    risk_devices = db.query(Device).filter(
        Device.risk_level.in_(["HIGH", "CRITICAL"]),
        Device.scan_source == "client"
    ).count()
    return {
        "device_count": device_count,
        "unacknowledged_alerts": alert_count,
        "risk_devices": risk_devices
    }


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/oui/status")
def oui_status():
    script = SCRIPT_DIR / "update_oui_multi.py"
    if script.exists():
        result = subprocess.run(
            [sys.executable, str(script), "status"],
            capture_output=True, text=True, timeout=10
        )
    else:
        script = SCRIPT_DIR / "update_oui.py"
        result = subprocess.run(
            [sys.executable, str(script), "status"],
            capture_output=True, text=True, timeout=10
        )
    try:
        import json
        return json.loads(result.stdout)
    except Exception:
        return {"error": result.stderr}


@router.post("/oui/update")
def oui_update():
    script = SCRIPT_DIR / "update_oui_multi.py"
    if not script.exists():
        script = SCRIPT_DIR / "update_oui.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        from app.services.vendor_lookup import VendorLookup
        VendorLookup().reload()
        import json
        try:
            return {"success": True, "message": result.stdout.strip()}
        except Exception:
            return {"success": True, "message": "Update completed"}
    else:
        return {"success": False, "error": result.stderr}
