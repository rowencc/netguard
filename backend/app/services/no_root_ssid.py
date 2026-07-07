"""
No-Root SSID Discovery Methods

These methods work without root/sudo permissions:
1. Networksetup WiFi info
2. System profiler WiFi data
3. DHCP lease correlation
4. HTTP User-Agent parsing
5. ARP table analysis with WiFi inference
"""

import subprocess
import json
import re
from typing import Dict, Optional, List


class NoRootSsidDiscovery:
    def __init__(self):
        self._current_ssid: Optional[str] = None
        self._ssid_cache: Dict[str, str] = {}

    def get_current_wifi_ssid(self) -> Optional[str]:
        if self._current_ssid:
            return self._current_ssid

        try:
            output = subprocess.check_output(
                ['networksetup', '-getairportnetwork', 'en0'],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5
            )
            if "You are not associated" not in output:
                if "Current Wi-Fi Network:" in output:
                    self._current_ssid = output.split("Current Wi-Fi Network:")[-1].strip()
                    return self._current_ssid
        except Exception:
            pass

        try:
            output = subprocess.check_output(
                ['networksetup', '-getairportnetwork', 'en1'],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5
            )
            if "You are not associated" not in output:
                if "Current Wi-Fi Network:" in output:
                    self._current_ssid = output.split("Current Wi-Fi Network:")[-1].strip()
                    return self._current_ssid
        except Exception:
            pass

        return None

    def get_available_networks(self) -> List[Dict]:
        networks = []
        try:
            output = subprocess.check_output(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10
            )
            lines = output.strip().split('\n')
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 6:
                        ssid = parts[0]
                        bssid = parts[1]
                        rssi = parts[2]
                        channel = parts[3]
                        if ssid:
                            networks.append({
                                "ssid": ssid,
                                "bssid": bssid,
                                "rssi": int(rssi) if rssi.lstrip('-').isdigit() else 0,
                                "channel": channel,
                            })
        except Exception:
            pass

        return networks

    def get_dhcp_lease_info(self) -> List[Dict]:
        leases = []

        lease_files = [
            "/var/db/dhcpclient/leases",
            "/private/var/db/dhcpclient/leases",
        ]

        for lease_file in lease_files:
            try:
                import urllib.request
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                url = f"file://{lease_file}"
                req = urllib.request.Request(url)
                response = urllib.request.urlopen(req, timeout=3, context=ctx)
                content = response.read().decode('utf-8', errors='ignore')

                for match in re.finditer(
                    r'\{(.*?)\}', content, re.DOTALL
                ):
                    lease_data = match.group(1)
                    lease = {}
                    for line in lease_data.split('\n'):
                        if 'IPAddress' in line:
                            lease['ip'] = line.split('=')[-1].strip()
                        elif 'HardwareAddress' in line:
                            lease['mac'] = line.split('=')[-1].strip()
                        elif 'Name' in line:
                            lease['hostname'] = line.split('=')[-1].strip()
                        elif 'SSID' in line:
                            lease['ssid'] = line.split('=')[-1].strip()
                    if lease:
                        leases.append(lease)
            except Exception:
                continue

        return leases

    def infer_ssid_from_arp(self, ip_address: str) -> Optional[str]:
        current_ssid = self.get_current_wifi_ssid()
        if not current_ssid:
            return None

        try:
            output = subprocess.check_output(
                ["arp", "-a", "-i", "en0"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10
            )
            for line in output.splitlines():
                if ip_address in line:
                    return current_ssid
        except Exception:
            pass

        return None

    def get_device_wifi_info(self, mac_address: str, ip_address: str) -> Dict:
        info = {
            "ssid": None,
            "current_network": None,
            "available_networks": [],
            "dhcp_info": None,
            "source": "none",
        }

        current_ssid = self.get_current_wifi_ssid()
        if current_ssid:
            info["current_network"] = current_ssid

        if ip_address:
            ssid = self.infer_ssid_from_arp(ip_address)
            if ssid:
                info["ssid"] = ssid
                info["source"] = "arp_inference"

        if mac_address in self._ssid_cache:
            info["ssid"] = self._ssid_cache[mac_address]
            info["source"] = "cache"

        leases = self.get_dhcp_lease_info()
        for lease in leases:
            if lease.get('mac', '').upper() == mac_address.upper():
                info['dhcp_info'] = lease
                if lease.get('ssid'):
                    info['ssid'] = lease['ssid']
                    info['source'] = 'dhcp'

        return info

    def scan_and_resolve(self, db_session) -> int:
        from app.models.device import Device

        devices = db_session.query(Device).filter(
            (Device.ssid == None) | (Device.ssid == "")
        ).all()

        current_ssid = self.get_current_wifi_ssid()
        updated = 0

        for device in devices:
            info = self.get_device_wifi_info(device.mac_address, device.ip_address)
            if info.get('ssid'):
                device.ssid = info['ssid']
                updated += 1

        db_session.commit()
        return updated


if __name__ == "__main__":
    discovery = NoRootSsidDiscovery()
    print("Current WiFi SSID:", discovery.get_current_wifi_ssid())
    print("Available networks:", len(discovery.get_available_networks()))
    print("DHCP leases:", len(discovery.get_dhcp_lease_info()))
