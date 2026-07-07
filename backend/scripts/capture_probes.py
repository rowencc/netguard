#!/usr/bin/env python3
"""
WiFi Probe Request Capture Script

Captures WiFi probe requests to extract SSID information.
Must be run with sudo: sudo python3 capture_probes.py

Usage:
    sudo python3 capture_probes.py                    # Capture for 60 seconds
    sudo python3 capture_probes.py --duration 120     # Capture for 120 seconds
    sudo python3 capture_probes.py --interface en0    # Specify interface
    sudo python3 capture_probes.py --output /tmp/probes.json  # Custom output
"""

import subprocess
import argparse
import json
import re
import time
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ProbeCapture:
    def __init__(self, interface: str = "en0", output_file: str = None):
        self.interface = interface
        self.output_file = output_file or "/tmp/wifi_probes.json"
        self.probes: Dict[str, Dict] = {}
        self.running = False

    def check_permissions(self) -> bool:
        if subprocess.run(["id", "-u"], capture_output=True).stdout.decode().strip() != "0":
            print("Error: This script must be run with sudo")
            print("Usage: sudo python3 capture_probes.py")
            return False
        return True

    def check_interface(self) -> bool:
        try:
            result = subprocess.run(
                ["ifconfig", self.interface],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"Error: Interface {self.interface} not found")
                return False
            return True
        except Exception:
            return False

    def capture_probes(self, duration: int = 60) -> Dict:
        print(f"Capturing WiFi probe requests on {self.interface} for {duration} seconds...")
        print("Press Ctrl+C to stop early\n")

        self.running = True
        start_time = time.time()

        try:
            proc = subprocess.Popen(
                [
                    "tcpdump", "-I", "-i", self.interface,
                    "-l", "-e",
                    "-v", "type mgt subtype probe-req"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            while self.running and (time.time() - start_time) < duration:
                line = proc.stdout.readline()
                if not line:
                    break

                self._parse_probe_line(line)

        except KeyboardInterrupt:
            print("\nCapture stopped by user")
        except Exception as e:
            print(f"Error during capture: {e}")
        finally:
            self.running = False
            if 'proc' in locals():
                try:
                    proc.kill()
                except Exception:
                    pass

        self._save_results()
        return self._get_stats()

    def _parse_probe_line(self, line: str):
        mac_match = re.search(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})', line)
        if not mac_match:
            return

        mac = mac_match.group(1).upper()

        ssid = ""
        ssid_match = re.search(r'SSID\s+(.+?)(?:\s+\(|$)', line)
        if ssid_match:
            ssid = ssid_match.group(1).strip()
            if ssid in ('<Any>', 'Broadcast', '(Broadcast)', ''):
                ssid = ""

        if not ssid:
            ssid_hex_match = re.search(r'0x([0-9a-fA-F]{2,})', line)
            if ssid_hex_match:
                hex_str = ssid_hex_match.group(1)
                try:
                    ssid = bytes.fromhex(hex_str).decode('utf-8', errors='ignore')
                    if not ssid or ssid.isspace():
                        ssid = ""
                except Exception:
                    ssid = ""

        if not ssid:
            ssid_ascii_match = re.search(r'"([^"]+)"', line)
            if ssid_ascii_match:
                ssid = ssid_ascii_match.group(1)

        rssi = 0
        rssi_match = re.search(r'signal\s+(-?\d+)', line)
        if rssi_match:
            rssi = int(rssi_match.group(1))

        if mac not in self.probes:
            self.probes[mac] = {
                "mac": mac,
                "ssids": [],
                "first_seen": datetime.now().isoformat(),
                "rssi_values": [],
            }

        if ssid and ssid not in self.probes[mac]["ssids"]:
            self.probes[mac]["ssids"].append(ssid)
            self.probes[mac]["last_ssid"] = ssid

        if rssi:
            self.probes[mac]["rssi_values"].append(rssi)
            self.probes[mac]["rssi_values"] = self.probes[mac]["rssi_values"][-10:]

        self.probes[mac]["last_seen"] = datetime.now().isoformat()
        self.probes[mac]["probe_count"] = self.probes[mac].get("probe_count", 0) + 1

    def _save_results(self):
        output_data = {
            "capture_time": datetime.now().isoformat(),
            "interface": self.interface,
            "device_count": len(self.probes),
            "devices": self.probes,
        }

        with open(self.output_file, 'w') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to {self.output_file}")

    def _get_stats(self) -> Dict:
        ssid_counts = {}
        for mac, info in self.probes.items():
            for ssid in info.get("ssids", []):
                ssid_counts[ssid] = ssid_counts.get(ssid, 0) + 1

        return {
            "total_devices": len(self.probes),
            "unique_ssids": len(ssid_counts),
            "ssid_distribution": ssid_counts,
            "output_file": self.output_file,
        }

    def stop(self):
        self.running = False


def load_captured_probes(filepath: str = "/tmp/wifi_probes.json") -> Dict:
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"devices": {}}


def get_ssid_for_mac(mac_address: str, filepath: str = "/tmp/wifi_probes.json") -> Optional[str]:
    data = load_captured_probes(filepath)
    mac_upper = mac_address.upper().replace("-", ":")

    devices = data.get("devices", {})

    if mac_upper in devices:
        return devices[mac_upper].get("last_ssid")

    for cached_mac, info in devices.items():
        if cached_mac.endswith(mac_upper[-8:]):
            return info.get("last_ssid")

    return None


def main():
    parser = argparse.ArgumentParser(description="Capture WiFi probe requests")
    parser.add_argument("--duration", "-d", type=int, default=60,
                        help="Capture duration in seconds (default: 60)")
    parser.add_argument("--interface", "-i", type=str, default="en0",
                        help="WiFi interface (default: en0)")
    parser.add_argument("--output", "-o", type=str, default="/tmp/wifi_probes.json",
                        help="Output file path")
    parser.add_argument("--query", "-q", type=str, default=None,
                        help="Query SSID for a specific MAC address")

    args = parser.parse_args()

    if args.query:
        ssid = get_ssid_for_mac(args.query, args.output)
        if ssid:
            print(f"MAC {args.query} -> SSID: {ssid}")
        else:
            print(f"No SSID found for MAC {args.query}")
        return

    capture = ProbeCapture(args.interface, args.output)

    if not capture.check_permissions():
        sys.exit(1)

    if not capture.check_interface():
        sys.exit(1)

    def signal_handler(sig, frame):
        print("\nStopping capture...")
        capture.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    stats = capture.capture_probes(args.duration)

    print("\n=== Capture Statistics ===")
    print(f"Total devices: {stats['total_devices']}")
    print(f"Unique SSIDs: {stats['unique_ssids']}")
    if stats['ssid_distribution']:
        print("\nSSID Distribution:")
        for ssid, count in sorted(stats['ssid_distribution'].items(), key=lambda x: -x[1]):
            print(f"  {ssid}: {count} devices")


if __name__ == "__main__":
    main()
