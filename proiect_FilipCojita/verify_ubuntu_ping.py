"""Module to ping multiple endpoints on Ubuntu and verify reachability."""

import subprocess
import sys
from typing import List


class UbuntuPingTester:
    """Class to ping multiple IP endpoints and verify connectivity."""

    def __init__(self, endpoints: List[str]) -> None:
        """
        Initialize with a list of IP addresses or hostnames.

        Args:
            endpoints (List[str]): List of IP addresses or hostnames to ping.
        """
        self.endpoints = endpoints

    def ping(self, ip: str) -> bool:
        """
        Ping a single IP address twice and print the result.

        Args:
            ip (str): IP address or hostname to ping.

        Returns:
            bool: True if ping succeeds, False otherwise.
        """
        print(f"Pinging {ip}...")
        result = subprocess.run(
            ['ping', '-c', '2', ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print(f"Ping to {ip} succeeded")
        else:
            print(f"Ping to {ip} failed")
            print(result.stderr.strip())
        return result.returncode == 0

    def verify_all(self) -> bool:
        """
        Ping all endpoints and verify if all are reachable.

        Returns:
            bool: True if all endpoints are reachable, False otherwise.
        """
        all_ok = True
        for ip_addr in self.endpoints:
            success = self.ping(ip_addr)
            print()  # Newline for clarity
            if not success:
                all_ok = False

        if all_ok:
            print("All endpoints reachable")
        else:
            print("One or more endpoints unreachable")

        return all_ok


def main() -> None:
    """Main function to create tester and verify endpoints."""
    endpoints_list = [
        '192.168.11.1',   # IOU1
        '192.168.101.2',  # CSR
        '192.168.102.2',  # IOSV
        '192.168.103.2',  # FTD
        '192.168.105.11', # Ubuntudockerguest-1
        '192.168.108.11', # DNS Server
        '192.168.109.11',  # Ubuntudockerguest-2
        '192.168.103.3'   #UbuntuDesktopGuest
    ]

    tester = UbuntuPingTester(endpoints_list)
    success = tester.verify_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
