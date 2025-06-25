"""Module to ping multiple endpoints on Ubuntu and verify reachability."""

import subprocess
import sys
import json
from typing import List, Tuple, Dict
from pyats.topology import loader


class UbuntuPingTester:
    """Class to ping multiple IP endpoints and verify connectivity."""

    def __init__(self, endpoints: List[str]) -> None:
        self.endpoints = endpoints
        self.results: Dict[str, Dict[str, str]] = {}

    def ping(self, ip: str) -> Tuple[str, bool]:
        """Ping a single IP address and store result in the results' dictionary."""
        print(f"\nPinging {ip} ...")
        result = subprocess.run(
            ['ping', '-c', '2', ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        success = result.returncode == 0

        self.results[ip] = {
            "status": "reachable" if success else "unreachable",
            "stdout": stdout,
            "stderr": stderr
        }

        print(stdout)
        if not success:
            print(stderr)

        return ip, success

    def verify_all(self) -> bool:
        failed = []
        succeeded = []
        for ip_addr in self.endpoints:
            ip, success = self.ping(ip_addr)
            if not success:
                failed.append(ip)
            else:
                succeeded.append(ip_addr)

        if not failed:
            print("\nAll endpoints are reachable!")
            return True
        else:
            print("\nSome endpoints failed to respond:")
            for ip in failed:
                print(f" - {ip}")
            print("Reachable endpoints:")
            for ip in succeeded:
                print(f" - {ip}")
            return False

    def write_results_to_json(self, filename: str = "ping_results.json") -> None:
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\nPing results written to {filename}")
        except Exception as e:
            print(f"\n[ERROR] Failed to write JSON file: {e}")


def extract_ips_from_testbed(testbed_path: str) -> List[str]:
    tb = loader.load(testbed_path)
    ips = []

    for device in tb.devices.values():
        for interface in device.interfaces.values():
            if hasattr(interface, 'ipv4') and interface.ipv4:
                ip_only = str(interface.ipv4.ip)
                ips.append(ip_only)

        dhcp_list = getattr(device.custom, "dhcp_assigned", [])
        if isinstance(dhcp_list, str):
            ips.append(dhcp_list)
        elif isinstance(dhcp_list, list):
            for ip in dhcp_list:
                ips.append(str(ip))

    return ips


def main():
    testbed_file = 'mytopo.yaml'
    endpoints = extract_ips_from_testbed(testbed_file)
    print("Collected endpoints to ping:", endpoints)

    tester = UbuntuPingTester(endpoints)
    success = tester.verify_all()
    tester.write_results_to_json("ping_results.json")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
