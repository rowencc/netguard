"""
WiFi Probe Request Analyzer

Captures WiFi probe requests to identify SSID associations.
When devices search for WiFi networks, they broadcast probe requests
containing the SSID they're looking for.

Requirements:
- macOS with WiFi adapter (en0)
- Monitor mode support
- Root/sudo permissions for packet capture

References:
- IEEE 802.11-2016: Wireless LAN MAC and PHY Specifications
- IEEE 802.11 Management Frames: Probe Request/Response
"""

import subprocess
import json
import re
import threading
import time
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime


class ProbeRequestAnalyzer:
    def __init__(self):
        self._ssid_map: Dict[str, str] = {}
        self._probe_cache: Dict[str, Dict] = {}
        self._capture_running = False
        self._capture_process = None

    def start_capture(self, interface: str = "en0", duration: int = 30) -> Dict:
        if self._capture_running:
            return {"status": "already_running", "message": "Capture already in progress"}

        self._capture_running = True
        self._probe_cache = {}

        def _capture_thread():
            try:
                proc = subprocess.Popen(
                    [
                        "tcpdump", "-I", "-i", interface,
                        "-w", "/tmp/probe_capture.pcap",
                        "-c", "1000",
                        "--time-stamp", "micro",
                        "type mgt subtype probe-req"
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=lambda: None
                )
                self._capture_process = proc
                proc.wait(timeout=duration)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except Exception:
                    pass
            except Exception:
                pass
            finally:
                self._capture_running = False
                self._parse_capture()

        thread = threading.Thread(target=_capture_thread, daemon=True)
        thread.start()

        return {"status": "started", "duration": duration, "interface": interface}

    def stop_capture(self) -> Dict:
        if self._capture_process:
            try:
                self._capture_process.kill()
            except Exception:
                pass
        self._capture_running = False
        return {"status": "stopped", "probe_count": len(self._probe_cache)}

    def _parse_capture(self):
        try:
            pcap_file = Path("/tmp/probe_capture.pcap")
            if not pcap_file.exists():
                return

            proc = subprocess.Popen(
                ["tcpdump", "-r", "/tmp/probe_capture.pcap", "-nn", "-e"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, _ = proc.communicate(timeout=30)

            for line in output.split('\n'):
                mac_match = re.search(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})', line)
                ssid_match = re.search(r'SSID\s+(.+?)(?:\s+|\t|$)', line)

                if mac_match and ssid_match:
                    mac = mac_match.group(1).upper()
                    ssid = ssid_match.group(1).strip()
                    if ssid and ssid != '<Any>' and ssid != '':
                        self._ssid_map[mac] = ssid
                        self._probe_cache[mac] = {
                            "ssid": ssid,
                            "timestamp": datetime.now().isoformat(),
                        }
        except Exception:
            pass

    def scan_probe_requests(self, interface: str = "en0", duration: int = 10) -> List[Dict]:
        try:
            proc = subprocess.Popen(
                [
                    "tcpdump", "-I", "-i", interface,
                    "-c", "100",
                    "--time-stamp", "micro",
                    "-e",
                    "type mgt subtype probe-req"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, _ = proc.communicate(timeout=duration + 5)

            results = []
            for line in output.split('\n'):
                mac_match = re.search(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})', line)
                if mac_match:
                    mac = mac_match.group(1).upper()
                    ssid = ""

                    ssid_hex_match = re.search(r'0x([0-9a-fA-F]+)', line)
                    if ssid_hex_match:
                        try:
                            ssid = bytes.fromhex(ssid_hex_match.group(1)).decode('utf-8', errors='ignore')
                        except Exception:
                            pass

                    if not ssid:
                        ssid_match = re.search(r'SSID\s+(.+?)(?:\s+|\t|$)', line)
                        if ssid_match:
                            ssid = ssid_match.group(1).strip()

                    if ssid and ssid not in ('<Any>', 'Broadcast', ''):
                        self._ssid_map[mac] = ssid
                        results.append({"mac": mac, "ssid": ssid})

            return results
        except Exception:
            return []

    def get_ssid_for_mac(self, mac_address: str) -> Optional[str]:
        mac_normalized = mac_address.upper().replace("-", ":")

        if mac_normalized in self._ssid_map:
            return self._ssid_map[mac_normalized]

        for cached_mac, ssid in self._ssid_map.items():
            if cached_mac.endswith(mac_normalized[-8:]):
                return ssid

        return None

    def get_all_probed_ssids(self) -> Dict[str, str]:
        return dict(self._ssid_map)

    def get_probe_stats(self) -> Dict:
        ssid_counts = {}
        for ssid in self._ssid_map.values():
            ssid_counts[ssid] = ssid_counts.get(ssid, 0) + 1

        return {
            "total_probes": len(self._probe_cache),
            "unique_devices": len(self._ssid_map),
            "unique_ssids": len(ssid_counts),
            "ssid_distribution": ssid_counts,
            "is_capturing": self._capture_running,
        }


class PassiveSsidDiscovery:
    def __init__(self):
        self.probe_analyzer = ProbeRequestAnalyzer()
        self._background_running = False

    def start_background_capture(self, interface: str = "en0", interval: int = 60):
        if self._background_running:
            return {"status": "already_running"}

        self._background_running = True

        def _background_thread():
            while self._background_running:
                try:
                    self.probe_analyzer.scan_probe_requests(interface, duration=15)
                except Exception:
                    pass
                time.sleep(interval)

        thread = threading.Thread(target=_background_thread, daemon=True)
        thread.start()

        return {"status": "started", "interval": interval}

    def stop_background_capture(self):
        self._background_running = False
        return {"status": "stopped"}

    def get_device_ssid(self, mac_address: str, ip_address: str = "") -> Optional[str]:
        ssid = self.probe_analyzer.get_ssid_for_mac(mac_address)
        if ssid:
            return ssid

        try:
            output = subprocess.check_output(
                ["arp", "-a", ip_address],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5
            )
            if ip_address in output:
                current_wifi = self._get_current_wifi()
                if current_wifi:
                    return current_wifi
        except Exception:
            pass

        return None

    def _get_current_wifi(self) -> Optional[str]:
        try:
            output = subprocess.check_output(
                ['networksetup', '-getairportnetwork', 'en0'],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5
            )
            if "You are not associated" not in output:
                if "Current Wi-Fi Network:" in output:
                    return output.split("Current Wi-Fi Network:")[-1].strip()
                return output.strip()
        except Exception:
            pass
        return None

    def scan_and_update_db(self, db_session):
        devices = db_session.query("Device").filter(
            (Device.ssid == None) | (Device.ssid == "")
        ).all()

        updated = 0
        for device in devices:
            ssid = self.get_device_ssid(device.mac_address, device.ip_address)
            if ssid:
                device.ssid = ssid
                updated += 1

        db_session.commit()
        return updated


if __name__ == "__main__":
    analyzer = ProbeRequestAnalyzer()
    print("Scanning for WiFi probe requests (10 seconds)...")
    results = analyzer.scan_probe_requests(duration=10)
    print(f"\nFound {len(results)} probe requests:")
    for r in results[:10]:
        print(f"  {r['mac']} -> SSID: {r['ssid']}")
    print(f"\nStats: {json.dumps(analyzer.get_probe_stats(), indent=2)}")
