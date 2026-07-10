from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from app.database import get_db
from app.models.device import Device
from app.models.scan_record import ScanRecord
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

DOCKER_IP_PREFIXES = ("172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.")

@router.get("/", response_model=List[dict])
def get_devices(
    skip: int = 0,
    limit: int = 200,
    risk_level: Optional[str] = None,
    scan_source: Optional[str] = None,
    client_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Device)
    if risk_level:
        query = query.filter(Device.risk_level == risk_level)
    if scan_source:
        query = query.filter(Device.scan_source == scan_source)
    if client_id:
        query = query.filter(Device.client_id == client_id)
    devices = query.offset(skip).limit(limit).all()
    result = []
    for d in devices:
        ip = d.ip_address or ""
        if ip.startswith(DOCKER_IP_PREFIXES):
            continue
        result.append({
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
            "client_id": d.client_id or '',
            "scan_source": d.scan_source or 'server',
            "first_seen": d.first_seen.isoformat() if d.first_seen else None,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None
        })
    return result


@router.get("/check-online")
def check_devices_online(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta

    devices = db.query(Device).filter(
        (Device.ip_address != None) & (Device.ip_address != "") &
        (Device.scan_source == "client")
    ).all()

    if not devices:
        return {"devices": [], "online_count": 0}

    now = datetime.now()
    threshold = timedelta(minutes=5)

    results = []
    online_count = 0
    for d in devices:
        if d.last_seen and (now - d.last_seen) < threshold:
            is_online = True
            online_count += 1
        else:
            is_online = False
        results.append({
            "id": d.id,
            "ip_address": d.ip_address,
            "is_online": is_online,
        })

    return {
        "devices": results,
        "online_count": online_count,
        "total_count": len(devices),
    }


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


@router.post("/scan-client")
async def scan_client(body: dict, db: Session = Depends(get_db)):
    from app.ws_manager import manager
    import uuid

    client_id = body.get("client_id")
    subnets = body.get("subnets", [])

    if not client_id:
        raise HTTPException(status_code=400, detail="client_id is required")

    if not manager.is_client_online(client_id):
        raise HTTPException(status_code=400, detail=f"Client {client_id} is not connected")

    scan_id = str(uuid.uuid4())

    record = ScanRecord(
        scan_id=scan_id,
        scan_type="client",
        client_id=client_id,
        status="pending",
    )
    db.add(record)
    db.commit()

    sent = await manager.send_to_client(client_id, {
        "type": "scan_command",
        "scan_id": scan_id,
        "subnets": subnets,
    })

    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send command to client")

    return {"status": "pending", "scan_id": scan_id, "client_id": client_id}


@router.post("/scan-browser")
def scan_browser(body: dict, db: Session = Depends(get_db)):
    client_ip = body.get("client_ip", "")
    browser_devices = body.get("devices", [])

    if not client_ip:
        raise HTTPException(status_code=400, detail="client_ip is required")

    if not browser_devices:
        raise HTTPException(status_code=400, detail="No devices provided from browser scan")

    existing_devices = db.query(Device).all()
    existing_ips = {d.ip_address: d for d in existing_devices}
    existing_macs = {d.mac_address.upper(): d for d in existing_devices if d.mac_address}

    new_count = 0
    scanned = 0
    alerts_created = 0

    for dev_data in browser_devices:
        ip = dev_data.get("ip_address", "")
        if not ip:
            continue

        scanned += 1
        hostname = dev_data.get("hostname", "")
        device_type = dev_data.get("device_type", "unknown")
        ports = dev_data.get("ports", [])

        # Browser can't get MAC addresses, generate a temporary one based on IP
        # Format: 02:XX:XX:XX:XX:XX where XX:XX:XX:XX is derived from IP (17 chars max)
        ip_parts = ip.split(".")
        if len(ip_parts) == 4:
            try:
                # Use last 4 bytes of IP, prefix with 02 (locally administered)
                temp_mac = f"02:{int(ip_parts[0]):02X}:{int(ip_parts[1]):02X}:{int(ip_parts[2]):02X}:{int(ip_parts[3]):02X}"
            except ValueError:
                temp_mac = f"02:00:00:00:{(scanned >> 8) & 0xFF:02X}:{scanned & 0xFF:02X}"
        else:
            temp_mac = f"02:00:00:00:{(scanned >> 8) & 0xFF:02X}:{scanned & 0xFF:02X}"

        # Try to identify device from ports
        identified = identifier.identify_device({
            "ip_address": ip,
            "mac_address": temp_mac,
            "hostname": hostname,
            "open_ports": {p: "" for p in ports}
        })
        vendor = identified.get("vendor", "")
        risk_level = identified.get("risk_level", "LOW")

        # Check if device already exists by IP
        existing = existing_ips.get(ip)
        if existing:
            existing.last_seen = func.now()
            if hostname:
                existing.hostname = hostname
                existing.hostname_source = "browser"
            if device_type and device_type != "unknown":
                existing.device_type = device_type
            if risk_level:
                existing.risk_level = risk_level
            existing.scan_source = "browser"
            device_id = existing.id
        else:
            # Check if MAC already exists (shouldn't happen with browser, but just in case)
            existing_by_mac = existing_macs.get(temp_mac.upper())
            if existing_by_mac:
                existing_by_mac.last_seen = func.now()
                existing_by_mac.ip_address = ip
                if hostname:
                    existing_by_mac.hostname = hostname
                    existing_by_mac.hostname_source = "browser"
                device_id = existing_by_mac.id
            else:
                new_device = Device(
                    mac_address=temp_mac,
                    mac_prefix=temp_mac[:8],
                    vendor=vendor,
                    device_type=device_type,
                    ip_address=ip,
                    hostname=hostname,
                    hostname_source="browser",
                    risk_level=risk_level,
                    scan_source="browser",
                )
                db.add(new_device)
                db.flush()
                device_id = new_device.id
                new_count += 1

        if risk_level in ("HIGH", "CRITICAL"):
            hostname_display = hostname or "--"
            vendor_display = vendor or "未知厂商"
            message = f"发现高风险设备: {device_type} ({vendor_display}) IP: {ip} 主机名: {hostname_display}"
            alerter.create_alert(
                device_id=device_id,
                alert_type="high_risk_device",
                severity="WARNING" if risk_level == "HIGH" else "CRITICAL",
                message=message,
            )
            alerts_created += 1

    db.commit()
    return {"device_count": scanned, "new_device_count": new_count, "alerts_created": alerts_created}


# In-memory scan status tracking
_scan_status = {}


@router.post("/scan-subnet")
def scan_subnet(body: dict, db: Session = Depends(get_db)):
    """
    Scan a specific subnet from the browser.
    The frontend detects the local IP via WebRTC, then calls this endpoint
    to perform a real ARP scan on the server side.
    """
    import uuid
    import threading

    subnet = body.get("subnet", "")
    client_ip = body.get("client_ip", "")

    if not subnet:
        raise HTTPException(status_code=400, detail="subnet is required (e.g. 192.168.1.0/24)")

    # Ensure subnet ends with /24
    if not subnet.endswith("/24"):
        ip_parts = subnet.split(".")
        if len(ip_parts) == 4:
            subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        else:
            raise HTTPException(status_code=400, detail="Invalid subnet format")

    scan_id = str(uuid.uuid4())
    _scan_status[scan_id] = {"status": "running", "subnet": subnet, "device_count": 0, "new_device_count": 0}

    def _do_scan():
        try:
            from app.database import SessionLocal
            from app.services.platform_compat import get_arp_table, ping_host
            from app.services.hostname_resolver import HostnameResolver
            from app.services.vendor_lookup import VendorLookup
            
            db_session = SessionLocal()
            try:
                existing_devices = db_session.query(Device).all()
                existing_ips = {d.ip_address: d for d in existing_devices}
                existing_macs = {d.mac_address.upper(): d for d in existing_devices if d.mac_address}

                # Step 1: Ping all IPs in the subnet to populate ARP table
                import subprocess
                ip_parts = subnet.split(".")
                subnet_prefix = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
                
                # Ping all IPs in parallel (fast, 0.5s timeout each)
                ping_ips = [f"{subnet_prefix}.{i}" for i in range(1, 255)]
                try:
                    # Use macOS ping -c 1 -t 0.5 for fast ping
                    proc = subprocess.Popen(
                        ["ping", "-c", "1", "-t", "0.3"] + ping_ips[:50],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    proc.wait(timeout=20)
                except Exception:
                    pass

                # Step 2: Read ARP table (no root needed)
                arp_devices = get_arp_table()
                
                # Filter to only the requested subnet
                subnet_devices = [
                    d for d in arp_devices 
                    if d["ip_address"].startswith(subnet_prefix)
                ]

                hostname_resolver = HostnameResolver(timeout=1.0)
                vendor_lookup = VendorLookup()
                
                new_count = 0
                scanned = 0
                alerts_created = 0

                for dev_data in subnet_devices:
                    mac = dev_data.get("mac_address", "")
                    ip = dev_data.get("ip_address", "")
                    if not ip or not mac:
                        continue

                    scanned += 1

                    # Fast hostname lookup
                    try:
                        hostname_result = hostname_resolver.resolve(ip)
                    except Exception:
                        hostname_result = {"hostname": "", "source": ""}
                    hostname = hostname_result.get("hostname", "")
                    hostname_source = hostname_result.get("source", "")
                    vendor = vendor_lookup.lookup(mac)
                    device_type = vendor_lookup.get_device_type_from_mac(mac) or "unknown"
                    risk_level = "LOW"

                    # Check if device already exists
                    existing = None
                    if mac:
                        existing = existing_macs.get(mac.upper())
                    if not existing:
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
                        if device_type and device_type != "unknown":
                            existing.device_type = device_type
                        existing.scan_source = "browser"
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
                            risk_level=risk_level,
                            scan_source="browser",
                        )
                        db_session.add(new_device)
                        db_session.flush()
                        device_id = new_device.id
                        new_count += 1

                    if risk_level in ("HIGH", "CRITICAL"):
                        hostname_display = hostname or "--"
                        vendor_display = vendor or "未知厂商"
                        message = f"发现高风险设备: {device_type} ({vendor_display}) IP: {ip} 主机名: {hostname_display}"
                        try:
                            alerter.create_alert(
                                device_id=device_id,
                                alert_type="high_risk_device",
                                severity="WARNING" if risk_level == "HIGH" else "CRITICAL",
                                message=message,
                            )
                            alerts_created += 1
                        except Exception:
                            pass

                    try:
                        db_session.commit()
                    except Exception:
                        db_session.rollback()

                _scan_status[scan_id] = {
                    "status": "complete",
                    "subnet": subnet,
                    "device_count": scanned,
                    "new_device_count": new_count,
                    "alerts_created": alerts_created
                }
            finally:
                db_session.close()
        except Exception as e:
            _scan_status[scan_id] = {"status": "error", "message": str(e)}

    thread = threading.Thread(target=_do_scan, daemon=True)
    thread.start()

    return {
        "scan_id": scan_id,
        "subnet": subnet,
        "status": "running"
    }


@router.get("/scan-subnet/{scan_id}")
def get_scan_status(scan_id: str):
    """Check the status of a subnet scan."""
    status = _scan_status.get(scan_id)
    if not status:
        raise HTTPException(status_code=404, detail="Scan not found")
    return status
