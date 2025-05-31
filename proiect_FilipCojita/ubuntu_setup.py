import subprocess
from typing import List

class UbuntuNetworkConfigurator:
    """
    Configure Ubuntu network interface and static routes.
    """

    def __init__(self, interface: str = 'ens4', ip: str = '192.168.11.21/24', gateway: str = '192.168.11.1') -> None:
        """
        Initialize configurator with interface, IP address, and gateway.
        """
        self.interface = interface
        self.ip = ip
        self.gateway = gateway
        self.routes = {
            "cloud": '192.168.12.0/24',
            "CSR": '192.168.101.0/24',
            "iosv": '192.168.102.0/24',
            "ftd": '192.168.103.0/24',
            "UbuntuDockerGuest-1": '192.168.105.0/24',
            "RouterLink-1": '192.168.106.0/24',
            "RouterLink-2": '192.168.107.0/24',
            "DNS-1": '192.168.108.0/24',
            "UbuntuDockerGuest-2": '192.168.109.0/24'
        }

    def run_command(self, cmd: List[str]) -> None:
        """
        Run system command and print output or error.
        """
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr.strip()}")
        else:
            print(f"Output: {result.stdout.strip()}")

    def configure(self) -> None:
        """
        Configure interface IP and add static routes.
        """
        print("Configuring Ubuntu interface and routes...")
        self.run_command(['sudo', 'ip', 'address', 'add', self.ip, 'dev', self.interface])
        self.run_command(['sudo', 'ip', 'link', 'set', self.interface, 'up'])

        for dest_name, subnet in self.routes.items():
            print(f"Adding route to {dest_name}: {subnet} via {self.gateway}")
            self.run_command(['sudo', 'ip', 'route', 'add', subnet, 'via', self.gateway])
        print("Ubuntu network configuration complete.")

if __name__ == "__main__":
    ubuntu = UbuntuNetworkConfigurator()
    ubuntu.configure()
