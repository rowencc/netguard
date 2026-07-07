from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from app.database import get_db
from app.models.device import Device
from app.services.scanner import NetworkScanner
from app.services.identifier import DeviceIdentifier
from app.services.vendor_lookup import VendorLookup
from app.services.mac_analyzer import MACAnalyzer
from app.services.alerter import AlertService
from app.services.hostname_resolver import HostnameResolver
from app.services.ssid_resolver import SSIDResolver
from app.services.h3c_resolver import H3CResolver, UniversalNetworkResolver
from app.services.passive_ssid import ProbeRequestAnalyzer, PassiveSsidDiscovery

router = APIRouter()
scanner = NetworkScanner()
identifier = DeviceIdentifier()
vendor_lookup = VendorLookup()
alerter = AlertService()
hostname_resolver = HostnameResolver()
ssid_resolver = SSIDResolver()
h3c_resolver = H3CResolver()
network_resolver = UniversalNetworkResolver()
probe_analyzer = ProbeRequestAnalyzer()
passive_ssid = PassiveSsidDiscovery()

@router.get("/", response_model=List[dict])
def get_devices(
    skip: int = 0,
    limit: int = 100,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Device)
    if risk_level:
        query = query.filter(Device.risk_level == risk_level)
    devices = query.offset(skip).limit(limit).all()
    return [
        {
            "id": d.id,
            "mac_address": d.mac_address,
            "mac_prefix": d.mac_prefix,
            "vendor": d.vendor,
            "device_type": d.device_type,
            "device_model": getattr(d, 'device_model', '') or '',
            "ip_address": d.ip_address,
            "hostname": d.hostname,
            "hostname_source": getattr(d, 'hostname_source', '') or '',
            "ssid": getattr(d, 'ssid', '') or '',
            "risk_level": d.risk_level,
            "is_authorized": d.is_authorized,
            "first_seen": d.first_seen.isoformat() if d.first_seen else None,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None
        }
        for d in devices
    ]

@router.get("/{device_id}")
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {
        "id": device.id,
        "mac_address": device.mac_address,
        "vendor": device.vendor,
        "device_type": device.device_type,
        "os_info": device.os_info,
        "ip_address": device.ip_address,
        "hostname": device.hostname,
        "first_seen": device.first_seen.isoformat() if device.first_seen else None,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "risk_level": device.risk_level,
        "is_authorized": device.is_authorized,
        "notes": device.notes
    }

@router.post("/scan")
def trigger_scan(network: Optional[str] = None, db: Session = Depends(get_db)):
    existing_devices = db.query(Device).all()
    existing_ips = {d.ip_address: d for d in existing_devices}

    import threading
    def _bg_resolve(devices_list):
        from app.database import SessionLocal
        bg_db = SessionLocal()
        try:
            for dev in devices_list:
                d = bg_db.query(Device).filter(Device.id == dev.id).first()
                if not d:
                    continue
                result = hostname_resolver.resolve(d.ip_address)
                hostname = result.get("hostname", "")
                if hostname and (not d.hostname or d.hostname_source in ("", "dns")):
                    d.hostname = hostname
                    d.hostname_source = result.get("source", "")
            bg_db.commit()
        except Exception:
            bg_db.rollback()
        finally:
            bg_db.close()

    no_hostname = [d for d in existing_devices if not d.hostname]
    if no_hostname:
        threading.Thread(target=_bg_resolve, args=(no_hostname,), daemon=True).start()

    devices = scanner.scan_network(network)
    new_count = 0
    scanned = 0
    alerts_created = 0
    for dev_data in devices:
        mac = dev_data.get("mac_address", "")
        if not mac:
            continue
        scanned += 1
        identified = identifier.identify_device(dev_data)
        ip = dev_data["ip_address"]
        vendor = identified.get("vendor", "")
        device_type = identified.get("device_type", "unknown")
        risk_level = identified.get("risk_level", "LOW")
        hostname = dev_data.get("hostname", "")
        hostname_source = dev_data.get("hostname_source", "")

        existing = existing_ips.get(ip)
        if existing:
            existing.last_seen = func.now()
            existing.mac_address = mac
            existing.mac_prefix = mac[:8]
            existing.ip_address = ip
            if hostname:
                existing.hostname = hostname
                existing.hostname_source = hostname_source
            if vendor:
                existing.vendor = vendor
            if device_type:
                existing.device_type = device_type
            if risk_level:
                existing.risk_level = risk_level
            device_id = existing.id
        else:
            new_device = Device(
                mac_address=mac,
                mac_prefix=mac[:8],
                vendor=vendor,
                device_type=device_type,
                ip_address=ip,
                hostname=hostname,
                hostname_source=hostname_source,
                os_info=identified.get("device_model", ""),
                risk_level=risk_level,
                is_authorized=False
            )
            db.add(new_device)
            db.flush()
            device_id = new_device.id
            new_count += 1

        if risk_level in ("HIGH", "CRITICAL"):
            hostname_display = hostname or "--"
            vendor_display = vendor or "未知厂商"
            type_display = device_type
            severity = "CRITICAL" if risk_level == "CRITICAL" else "WARNING"
            message = f"发现高风险设备: {type_display} ({vendor_display}) IP: {ip} 主机名: {hostname_display}"
            alerter.create_alert(
                device_id=device_id,
                alert_type="high_risk_device",
                severity=severity,
                message=message
            )
            alerts_created += 1
    db.commit()
    return {"device_count": scanned, "new_device_count": new_count, "alerts_created": alerts_created}

@router.put("/{device_id}")
def update_device(
    device_id: int,
    is_authorized: Optional[bool] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if is_authorized is not None:
        device.is_authorized = is_authorized
    if notes is not None:
        device.notes = notes
    db.commit()
    return {"message": "Device updated"}


@router.post("/{device_id}/deep-scan")
def deep_scan_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    result = scanner.deep_scan(device.ip_address)
    if not result:
        return {"message": "Scan returned no results", "ip": device.ip_address}
    vendor = result.get("vendor") or device.vendor
    identified = identifier.identify_device({
        "ip_address": device.ip_address,
        "mac_address": device.mac_address,
        "hostname": device.hostname or "",
        "vendor": vendor,
        "os_matches": result.get("os_matches", []),
        "open_ports": result.get("open_ports", {})
    })
    if vendor:
        device.vendor = vendor
    if identified.get("device_type"):
        device.device_type = identified["device_type"]
    if identified.get("risk_level"):
        device.risk_level = identified["risk_level"]
    if identified.get("device_model"):
        device.os_info = identified["device_model"]
    db.commit()
    return {
        "ip": device.ip_address,
        "vendor": vendor,
        "device_type": device.device_type,
        "risk_level": device.risk_level,
        "open_ports": result.get("open_ports", {}),
        "os_matches": result.get("os_matches", [])
    }


@router.get("/lookup/{mac_address}")
def lookup_mac(mac_address: str):
    result = vendor_lookup.lookup_detailed(mac_address)
    vendor = result.get("vendor")
    if not vendor:
        mac_info = MACAnalyzer.get_mac_info(mac_address)
        return {
            "mac_address": mac_address,
            "vendor": None,
            "device_type": "unknown",
            "source": result.get("source"),
            "confidence": 0.0,
            "mac_info": mac_info,
        }
    identified = identifier.identify_device({
        "mac_address": mac_address,
        "hostname": "",
        "vendor": vendor
    })
    return {
        "mac_address": mac_address,
        "vendor": vendor,
        "source": result.get("source"),
        "confidence": result.get("confidence", 0.0),
        "alternatives": result.get("alternatives", []),
        "device_type": identified.get("device_type", "unknown"),
        "risk_level": identified.get("risk_level", "LOW"),
        "mac_info": identified.get("mac_info", {}),
        "is_randomized": identified.get("is_randomized_mac", False),
    }


@router.get("/analyze/{mac_address}")
def analyze_mac(mac_address: str):
    analysis = MACAnalyzer.analyze(mac_address)
    return {
        "mac_address": analysis.mac_address,
        "normalized": analysis.normalized,
        "is_valid": analysis.is_valid,
        "oui": analysis.oui,
        "nic_specific": analysis.nic_specific,
        "is_multicast": analysis.is_multicast,
        "is_locally_administered": analysis.is_locally_administered,
        "is_burned_in_address": analysis.is_burned_in,
        "mac_type": analysis.mac_type,
        "broadcast": analysis.broadcast,
        "bit_summary": analysis.bit_summary,
        "global_range": analysis.global_range,
        "local_range": analysis.local_range,
    }


@router.get("/validate/{mac_address}")
def validate_vendor(mac_address: str, vendor: str):
    validation = vendor_lookup.cross_validate(mac_address, vendor)
    mac_info = MACAnalyzer.get_mac_info(mac_address)
    return {
        "mac_address": mac_address,
        "mac_info": mac_info,
        "validation": validation,
    }


@router.post("/{device_id}/resolve-hostname")
def resolve_device_hostname(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    result = hostname_resolver.resolve(device.ip_address)
    hostname = result.get("hostname", "")
    source = result.get("source", "")
    confidence = result.get("confidence", 0.0)
    
    if hostname:
        device.hostname = hostname
        device.hostname_source = source
        db.commit()
    
    return {
        "device_id": device_id,
        "ip_address": device.ip_address,
        "hostname": hostname,
        "hostname_source": source,
        "confidence": confidence,
    }


@router.post("/resolve-all-hostnames")
def resolve_all_hostnames(db: Session = Depends(get_db)):
    import threading
    
    devices = db.query(Device).filter(
        (Device.hostname == None) | (Device.hostname == "")
    ).limit(20).all()
    
    def _resolve_background(device_ids):
        from app.database import SessionLocal
        db_session = SessionLocal()
        try:
            for did in device_ids:
                device = db_session.query(Device).filter(Device.id == did).first()
                if not device:
                    continue
                result = hostname_resolver.resolve(device.ip_address)
                hostname = result.get("hostname", "")
                if hostname:
                    device.hostname = hostname
                    device.hostname_source = result.get("source", "")
            db_session.commit()
        except Exception:
            db_session.rollback()
        finally:
            db_session.close()
    
    device_ids = [d.id for d in devices]
    if device_ids:
        thread = threading.Thread(target=_resolve_background, args=(device_ids,))
        thread.daemon = True
        thread.start()
    
    return {"message": f"Started resolving {len(device_ids)} devices", "device_count": len(device_ids)}


@router.get("/wifi/networks")
def get_wifi_networks():
    return ssid_resolver.get_network_info()


@router.get("/wifi/clients")
def get_wifi_clients():
    clients = network_resolver.get_all_clients()
    return {"clients": clients, "count": len(clients)}


@router.get("/network/type")
def detect_network_type():
    network_type = network_resolver.detect_network_type("192.168.100.1")
    return {"type": network_type, "gateway": "192.168.100.1"}


@router.post("/resolve-ssids")
def resolve_all_ssids(db: Session = Depends(get_db)):
    import threading

    def _resolve_ssid_background():
        from app.database import SessionLocal
        db_session = SessionLocal()
        try:
            clients = network_resolver.get_all_clients()
            mac_to_ssid = {c["mac"].upper(): c.get("ssid", "") for c in clients if c.get("ssid")}

            devices = db_session.query(Device).filter(
                (Device.ssid == None) | (Device.ssid == "")
            ).all()
            for device in devices:
                ssid = mac_to_ssid.get(device.mac_address.upper())
                if ssid:
                    device.ssid = ssid
                else:
                    ssid = ssid_resolver.get_ssid_for_device(device.mac_address, device.ip_address)
                    if ssid:
                        device.ssid = ssid
            db_session.commit()
        except Exception:
            db_session.rollback()
        finally:
            db_session.close()

    thread = threading.Thread(target=_resolve_ssid_background, daemon=True)
    thread.start()

    return {"message": "Started resolving SSIDs"}


@router.post("/wifi/probe/start")
def start_probe_capture(interface: str = "en0", duration: int = 30):
    return probe_analyzer.start_capture(interface, duration)


@router.post("/wifi/probe/stop")
def stop_probe_capture():
    return probe_analyzer.stop_capture()


@router.get("/wifi/probe/scan")
def scan_probe_requests(interface: str = "en0", duration: int = 10):
    results = probe_analyzer.scan_probe_requests(interface, duration)
    return {"probes": results, "count": len(results)}


@router.get("/wifi/probe/stats")
def get_probe_stats():
    return probe_analyzer.get_probe_stats()


@router.get("/wifi/probe/ssids")
def get_all_probed_ssids():
    ssids = probe_analyzer.get_all_probed_ssids()
    return {"ssids": ssids, "count": len(ssids)}


@router.post("/wifi/probe/resolve")
def resolve_ssids_via_probes(db: Session = Depends(get_db)):
    import threading

    def _resolve_via_probes():
        from app.database import SessionLocal
        from app.services.passive_ssid import ProbeRequestAnalyzer
        db_session = SessionLocal()
        try:
            devices = db_session.query(Device).filter(
                (Device.ssid == None) | (Device.ssid == "")
            ).all()

            probe_analyzer.scan_probe_requests(duration=15)

            updated = 0
            for device in devices:
                ssid = probe_analyzer.get_ssid_for_mac(device.mac_address)
                if ssid:
                    device.ssid = ssid
                    updated += 1

            db_session.commit()
        except Exception:
            db_session.rollback()
        finally:
            db_session.close()

    thread = threading.Thread(target=_resolve_via_probes, daemon=True)
    thread.start()

    return {"message": "Started resolving SSIDs via probe requests"}


@router.post("/wifi/probe/run-capture")
def run_probe_capture_script(duration: int = 60):
    import threading

    def _run_capture():
        try:
            subprocess.run(
                ["python3", "/Users/rowen/IdeaProjects/mimoProject/netguard/backend/scripts/capture_probes.py",
                 "--duration", str(duration)],
                timeout=duration + 10,
                capture_output=True
            )
        except Exception:
            pass

    thread = threading.Thread(target=_run_capture, daemon=True)
    thread.start()

    return {
        "message": "Probe capture started",
        "duration": duration,
        "note": "Run with sudo: sudo python3 backend/scripts/capture_probes.py --duration " + str(duration),
        "output_file": "/tmp/wifi_probes.json"
    }


@router.get("/wifi/probe/from-file")
def get_probes_from_file():
    import json as json_mod
    from pathlib import Path

    probe_file = Path("/tmp/wifi_probes.json")
    if probe_file.exists():
        with open(probe_file) as f:
            data = json_mod.load(f)
        return {
            "capture_time": data.get("capture_time"),
            "device_count": data.get("device_count", 0),
            "devices": data.get("devices", {}),
        }
    return {"error": "No probe data found. Run capture first.", "file": "/tmp/wifi_probes.json"}


@router.post("/wifi/probe/resolve-from-file")
def resolve_ssids_from_probe_file(db: Session = Depends(get_db)):
    import json as json_mod
    from pathlib import Path

    probe_file = Path("/tmp/wifi_probes.json")
    if not probe_file.exists():
        return {"error": "No probe data found. Run capture first."}

    with open(probe_file) as f:
        data = json_mod.load(f)

    devices_data = data.get("devices", {})

    mac_to_ssid = {}
    for mac, info in devices_data.items():
        if info.get("ssids"):
            mac_to_ssid[mac.upper()] = info["ssids"][0]

    updated = 0
    for device in db.query(Device).filter(
        (Device.ssid == None) | (Device.ssid == "")
    ).all():
        ssid = mac_to_ssid.get(device.mac_address.upper())
        if ssid:
            device.ssid = ssid
            updated += 1

    db.commit()

    return {
        "message": f"Updated {updated} devices with SSID from probe file",
        "updated_count": updated,
        "total_probed": len(mac_to_ssid),
    }


@router.get("/check-online")
def check_devices_online(db: Session = Depends(get_db)):
    import concurrent.futures
    from app.services.platform_compat import ping_host

    devices = db.query(Device).filter(
        (Device.ip_address != None) & (Device.ip_address != "")
    ).all()

    if not devices:
        return {"devices": [], "online_count": 0}

    ip_list = [(d.id, d.ip_address) for d in devices]
    online_ids = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_id = {
            executor.submit(ping_host, ip): dev_id
            for dev_id, ip in ip_list
        }
        try:
            for future in concurrent.futures.as_completed(future_to_id, timeout=15):
                dev_id = future_to_id[future]
                try:
                    if future.result():
                        online_ids.add(dev_id)
                except Exception:
                    pass
        except TimeoutError:
            for future, dev_id in future_to_id.items():
                if future.done():
                    try:
                        if future.result():
                            online_ids.add(dev_id)
                    except Exception:
                        pass

    results = []
    for d in devices:
        is_online = d.id in online_ids
        if is_online:
            d.last_seen = func.now()
        results.append({
            "id": d.id,
            "ip_address": d.ip_address,
            "is_online": is_online,
        })

    db.commit()

    return {
        "devices": results,
        "online_count": len(online_ids),
        "total_count": len(devices),
    }
