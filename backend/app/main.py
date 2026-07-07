import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from app.config import config
from app.api import devices, alerts, system, libraries
from app.ws_manager import manager
from app.database import engine, SessionLocal, Base
from app.models import Device, Alert, ScanRecord, Client

app = FastAPI(
    title=config["app"]["name"],
    version=config["app"]["version"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(libraries.router, prefix="/api/libraries", tags=["libraries"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "NetGuard API"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.post("/api/sync/heartbeat")
def sync_heartbeat(body: dict):
    db = SessionLocal()
    try:
        client_id = body.get("client_id", "")
        client = db.query(Client).filter(Client.client_id == client_id).first()
        if not client:
            client = Client(client_id=client_id)
            db.add(client)
        client.hostname = body.get("hostname", "")
        client.ip_address = body.get("ip_address", "")
        client.platform = body.get("platform", "")
        client.version = body.get("version", "")
        client.device_count = body.get("device_count", 0)
        client.online_count = body.get("online_count", 0)
        client.last_heartbeat = func.now()
        client.is_online = True
        db.commit()

        if client_id not in manager._client_info:
            manager._client_info[client_id] = {
                "hostname": client.hostname,
                "ip_address": client.ip_address,
                "platform": client.platform,
            }

        return {"status": "ok", "server_time": datetime.now().isoformat()}
    finally:
        db.close()

@app.post("/api/sync/report-devices")
def sync_report_devices(body: list):
    db = SessionLocal()
    try:
        new_devices = 0
        updated_devices = 0
        alerts_created = 0

        for report in body:
            mac = report.get("mac_address", "").upper()
            if not mac:
                continue

            client_id = report.get("client_id", "")
            existing = db.query(Device).filter(Device.mac_address == mac).first()

            if existing:
                existing.ip_address = report.get("ip_address", existing.ip_address)
                existing.hostname = report.get("hostname") or existing.hostname
                existing.vendor = report.get("vendor") or existing.vendor
                existing.device_type = report.get("device_type") or existing.device_type
                existing.risk_level = report.get("risk_level", existing.risk_level)
                existing.last_seen = func.now()
                existing.client_id = client_id
                existing.scan_source = "client"
                updated_devices += 1
            else:
                mac_prefix = mac[:8] if len(mac) >= 8 else mac
                new_device = Device(
                    mac_address=mac,
                    mac_prefix=mac_prefix,
                    ip_address=report.get("ip_address", ""),
                    hostname=report.get("hostname", ""),
                    vendor=report.get("vendor", ""),
                    device_type=report.get("device_type", "unknown"),
                    risk_level=report.get("risk_level", "LOW"),
                    client_id=client_id,
                    scan_source="client",
                )
                db.add(new_device)
                new_devices += 1

            if report.get("risk_level") in ("HIGH", "CRITICAL"):
                alerts_created += 1

        db.commit()
        return {
            "status": "ok",
            "new_devices": new_devices,
            "updated_devices": updated_devices,
            "alerts_created": alerts_created,
        }
    finally:
        db.close()

@app.get("/api/sync/commands/{client_id}")
def sync_commands(client_id: str):
    db = SessionLocal()
    try:
        client = db.query(Client).filter(Client.client_id == client_id).first()
        if client:
            client.last_heartbeat = func.now()
            db.commit()
    finally:
        db.close()
    return {"commands": [], "config": {"scan_interval": 300, "alert_threshold": "MEDIUM"}}

@app.get("/api/clients")
def list_clients():
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        online_client_ids = set(manager._client_info.keys())
        result = []
        for c in clients:
            result.append({
                "client_id": c.client_id,
                "hostname": c.hostname,
                "ip_address": c.ip_address,
                "platform": c.platform,
                "version": c.version,
                "is_online": c.client_id in online_client_ids,
                "device_count": c.device_count,
                "online_count": c.online_count,
                "last_heartbeat": c.last_heartbeat.isoformat() if c.last_heartbeat else None,
                "last_scan": c.last_scan.isoformat() if c.last_scan else None,
            })
        return result
    finally:
        db.close()

@app.websocket("/ws/client/{client_id}")
async def ws_client(websocket: WebSocket, client_id: str):
    db = SessionLocal()
    try:
        client = db.query(Client).filter(Client.client_id == client_id).first()
        info = {
            "hostname": client.hostname if client else "",
            "ip_address": client.ip_address if client else "",
            "platform": client.platform if client else "",
        }
    finally:
        db.close()

    await manager.connect_client(websocket, client_id, info)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "heartbeat":
                db = SessionLocal()
                try:
                    client = db.query(Client).filter(Client.client_id == client_id).first()
                    if client:
                        client.last_heartbeat = func.now()
                        client.device_count = data.get("device_count", 0)
                        client.online_count = data.get("online_count", 0)
                        db.commit()
                finally:
                    db.close()
                await websocket.send_json({"type": "heartbeat_ack"})

            elif msg_type == "scan_result":
                scan_id = data.get("scan_id")
                device_data = data.get("device", {})
                is_online = device_data.get("is_online", True)

                db = SessionLocal()
                try:
                    mac = device_data.get("mac_address", "").upper()
                    existing = db.query(Device).filter(Device.mac_address == mac).first()
                    if existing:
                        existing.ip_address = device_data.get("ip_address", existing.ip_address)
                        existing.hostname = device_data.get("hostname") or existing.hostname
                        existing.vendor = device_data.get("vendor") or existing.vendor
                        existing.device_type = device_data.get("device_type") or existing.device_type
                        existing.risk_level = device_data.get("risk_level", existing.risk_level)
                        existing.last_seen = func.now()
                        existing.client_id = client_id
                        existing.scan_source = "client"
                    else:
                        mac_prefix = mac[:8] if len(mac) >= 8 else mac
                        new_device = Device(
                            mac_address=mac,
                            mac_prefix=mac_prefix,
                            ip_address=device_data.get("ip_address", ""),
                            hostname=device_data.get("hostname", ""),
                            vendor=device_data.get("vendor", ""),
                            device_type=device_data.get("device_type", "unknown"),
                            risk_level=device_data.get("risk_level", "LOW"),
                            client_id=client_id,
                            scan_source="client",
                        )
                        db.add(new_device)
                    db.commit()
                finally:
                    db.close()

                await manager.broadcast_scan_result(scan_id, client_id, {
                    "status": "device_found",
                    "device": device_data
                })

            elif msg_type == "scan_complete":
                scan_id = data.get("scan_id")
                db = SessionLocal()
                try:
                    record = db.query(ScanRecord).filter(ScanRecord.scan_id == scan_id).first()
                    if record:
                        record.status = "done"
                        record.device_count = data.get("device_count", 0)
                        record.new_device_count = data.get("new_device_count", 0)
                        record.completed_at = func.now()
                        db.commit()
                    client = db.query(Client).filter(Client.client_id == client_id).first()
                    if client:
                        client.last_scan = func.now()
                        db.commit()
                finally:
                    db.close()

                await manager.broadcast_scan_result(scan_id, client_id, {
                    "status": "complete",
                    "device_count": data.get("device_count", 0),
                    "new_device_count": data.get("new_device_count", 0),
                })

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect_client(client_id)

@app.websocket("/ws/frontend")
async def ws_frontend(websocket: WebSocket):
    await manager.connect_frontend(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "scan_request":
                client_id = msg.get("client_id")
                subnets = msg.get("subnets", [])

                import uuid
                scan_id = str(uuid.uuid4())

                db = SessionLocal()
                try:
                    record = ScanRecord(
                        scan_id=scan_id,
                        scan_type="client",
                        client_id=client_id,
                        status="pending",
                    )
                    db.add(record)
                    db.commit()
                finally:
                    db.close()

                sent = await manager.send_to_client(client_id, {
                    "type": "scan_command",
                    "scan_id": scan_id,
                    "subnets": subnets,
                })

                if sent:
                    await websocket.send_json({
                        "type": "scan_initiated",
                        "scan_id": scan_id,
                        "client_id": client_id,
                    })
                else:
                    await websocket.send_json({
                        "type": "scan_error",
                        "error": f"Client {client_id} is not connected",
                    })

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect_frontend(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8089)
