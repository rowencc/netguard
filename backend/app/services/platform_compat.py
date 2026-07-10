"""
Cross-platform compatibility utilities.

Supports:
- macOS (development)
- Ubuntu/Debian Linux (production on mini PC hardware)
"""

import sys
import subprocess
import socket
from typing import List, Optional, Dict
from functools import lru_cache


@lru_cache()
def get_platform() -> str:
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "linux":
        return "linux"
    return "unknown"


def is_macos() -> bool:
    return get_platform() == "macos"


def is_linux() -> bool:
    return get_platform() == "linux"


def get_default_interface() -> str:
    if is_macos():
        return "en0"
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.splitlines():
            if "dev" in line:
                parts = line.split()
                idx = parts.index("dev")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    except Exception:
        pass
    return "eth0"


def get_all_interfaces() -> List[str]:
    if is_macos():
        return ["en0", "en1", "en2", "en3"]
    try:
        result = subprocess.run(
            ["ls", "/sys/class/net/"],
            capture_output=True, text=True, timeout=3
        )
        ifaces = []
        for line in result.stdout.splitlines():
            name = line.strip()
            if name and name != "lo":
                ifaces.append(name)
        return ifaces if ifaces else ["eth0", "wlan0"]
    except Exception:
        return ["eth0", "wlan0"]


def get_arp_table() -> List[Dict[str, str]]:
    devices = []
    seen = set()

    # 只从物理网络接口获取 ARP 表
    interfaces = []
    if is_macos():
        interfaces = ["en0", "en1", "en2", "en3"]
    else:
        # Linux: 只取非 Docker 虚拟接口
        try:
            result = subprocess.run(
                ["ip", "-o", "link", "show"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                # 格式: "2: eth0: <BROADCAST,..."
                parts = line.split()
                if len(parts) >= 2:
                    iface = parts[1].rstrip(':')
                    # 排除 Docker/虚拟接口
                    if not any(x in iface for x in ['docker', 'br-', 'veth', 'virbr', 'lo']):
                        interfaces.append(iface)
        except Exception:
            interfaces = ["eth0", "ens3", "eno1"]

    for iface in interfaces:
        try:
            if is_macos():
                proc = subprocess.Popen(
                    ["arp", "-a", "-i", iface],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                output, _ = proc.communicate(timeout=10)
            else:
                result = subprocess.run(
                    ["arp", "-i", iface, "-an"],
                    capture_output=True, text=True, timeout=10
                )
                output = result.stdout

            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    ip = parts[1].strip("()") if is_macos() else parts[1].strip("()")
                    mac = parts[3]
                    
                    # 过滤无效条目
                    if "incomplete" in mac.lower():
                        continue
                    if mac == "ff:ff:ff:ff:ff:ff":
                        continue
                    # 过滤组播 MAC (01:00:5e, 33:33, ff:ff)
                    mac_lower = mac.lower()
                    if mac_lower.startswith(("01:00:5e", "33:33", "ff:ff")):
                        continue
                    # 过滤回环和链路本地地址
                    if ip.startswith(("127.", "169.254.")):
                        continue
                    # 过滤 Docker/虚拟网络
                    if ip.startswith(("172.17.", "172.18.", "172.19.", "172.20.")):
                        continue
                    
                    if ip not in seen:
                        seen.add(ip)
                        devices.append({"ip_address": ip, "mac_address": mac.upper()})
        except Exception:
            continue

    return devices


def ping_host(ip: str, timeout: int = 2) -> bool:
    try:
        if is_macos():
            result = subprocess.run(
                ["ping", "-c", "1", "-t", str(timeout), ip],
                capture_output=True, timeout=timeout + 1
            )
        else:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", str(timeout), ip],
                capture_output=True, timeout=timeout + 1
            )
        return result.returncode == 0
    except Exception:
        return False


def get_wifi_ssid() -> Optional[str]:
    if is_macos():
        try:
            result = subprocess.run(
                ["networksetup", "-getairportnetwork", "en0"],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            if "You are not associated" not in output and "AirPort" not in output:
                ssid = output.replace("Current Wi-Fi Network: ", "").strip()
                if ssid:
                    return ssid
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework"
                 "/Versions/Current/Resources/airport", "-I"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if " SSID:" in line:
                    ssid = line.split("SSID:")[-1].strip()
                    if ssid:
                        return ssid
        except Exception:
            pass
    else:
        try:
            result = subprocess.run(
                ["iwgetid", "-r"],
                capture_output=True, text=True, timeout=5
            )
            ssid = result.stdout.strip()
            if ssid:
                return ssid
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if line.startswith("yes:"):
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass

        try:
            default_iface = get_default_interface()
            result = subprocess.run(
                ["iw", "dev", default_iface, "link"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "SSID:" in line:
                    return line.split("SSID:")[-1].strip()
        except Exception:
            pass

    return None


def scan_wifi_networks() -> List[Dict]:
    networks = []

    if is_macos():
        try:
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework"
                 "/Versions/Current/Resources/airport", "-s"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2:
                    ssid = parts[0]
                    bssid = parts[1] if len(parts) > 1 else ""
                    rssi = parts[2] if len(parts) > 2 else ""
                    channel = parts[3] if len(parts) > 3 else ""
                    if ssid:
                        networks.append({
                            "ssid": ssid,
                            "bssid": bssid,
                            "rssi": int(rssi) if rssi.lstrip("-").isdigit() else 0,
                            "channel": channel,
                        })
        except Exception:
            pass
    else:
        try:
            default_iface = get_default_interface()
            result = subprocess.run(
                ["nmcli", "-t", "-f",
                 "SSID,BSSID,SIGNAL,CHAN", "dev", "wifi", "list",
                 "ifname", default_iface],
                capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.splitlines():
                parts = line.split(":")
                if len(parts) >= 3:
                    ssid = parts[0]
                    bssid = parts[1]
                    signal = parts[2]
                    channel = parts[3] if len(parts) > 3 else ""
                    if ssid:
                        networks.append({
                            "ssid": ssid,
                            "bssid": bssid,
                            "rssi": int(signal) if signal.isdigit() else 0,
                            "channel": channel,
                        })
        except Exception:
            pass

    return networks


def get_network_info() -> Dict:
    info = {
        "platform": get_platform(),
        "default_interface": get_default_interface(),
        "interfaces": get_all_interfaces(),
        "ssid": get_wifi_ssid(),
        "hostname": socket.gethostname(),
    }

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["local_ip"] = s.getsockname()[0]
        s.close()
    except Exception:
        info["local_ip"] = "127.0.0.1"

    return info
