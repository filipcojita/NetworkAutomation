import logging
import subprocess
from pyats.topology import Device, loader
from ipaddress import IPv4Network

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, encoding='utf-8')


class UbuntuNetworkConfigurator:
    """
    Automates the configuration of an Ubuntu device's network interface and static routes
    using parameters provided via a pyATS testbed Device object.

    Attributes:
        device (Device): The pyATS Device object representing the Ubuntu host.
        name (str): The device's name.
        interface (str): Network interface to configure (e.g., 'ens4').
        ip (str): IP address to assign to the interface.
        gateway (str): Default gateway IP address.
        routes (dict): A dictionary of static routes to be added.
    """

    def __init__(self, device: Device, testbed_path: str = None):
        """
        Initializes the configurator using custom attributes defined under the device.
        If routes are not provided, attempts to generate them from the testbed topology.

        Args:
            device (Device): pyATS device representing the Ubuntu system.
            testbed_path (str, optional): Path to the testbed file for route discovery.
        """
        self.device = device
        self.name = device.name
        custom = device.custom.get('network_config', {})

        self.interface = custom.get('interface')
        self.ip = custom.get('ip')
        self.gateway = custom.get('gateway')
        self.routes = custom.get('routes', {})

        # Ensure mandatory fields are provided
        if not all([self.interface, self.ip, self.gateway]):
            raise ValueError(f"Missing required config values for {self.name}")

        # Auto-generate routes if missing and testbed is provided
        if not self.routes and testbed_path:
            self.routes = self.generate_routes_from_testbed(testbed_path, self.name)

    def run_command(self, cmd):
        """
        Executes a shell command using subprocess and logs the result.

        Args:
            cmd (list): The command to execute as a list of arguments.
        """
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"Error: {result.stderr.strip()}")
        else:
            logger.debug(f"Output: {result.stdout.strip()}")

    def route_exists(self, destination: str) -> bool:
        """
        Checks if a route to the given destination already exists.

        Args:
            destination (str): The destination subnet (e.g., '192.168.111.0/24').

        Returns:
            bool: True if the route exists, False otherwise.
        """
        result = subprocess.run(['ip', 'route', 'show', destination],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return destination in result.stdout

    def configure(self):
        """
        Configures the Ubuntu network interface and adds static routes.
        - Assigns IP to the interface.
        - Brings the interface up.
        - Adds routes if they don't already exist.
        """
        self.run_command(['sudo', 'ip', 'address', 'add', self.ip, 'dev', self.interface])
        self.run_command(['sudo', 'ip', 'link', 'set', self.interface, 'up'])

        for label, subnet in self.routes.items():
            if not self.route_exists(subnet):
                self.run_command(['sudo', 'ip', 'route', 'add', subnet, 'via', self.gateway])

        logger.info(f"Finished configuration for Ubuntu device: {self.name}")

    @staticmethod
    def generate_routes_from_testbed(testbed_path: str, ubuntu_device_name: str) -> dict:
        """
        Generates a dictionary of unique /24 routes based on the IPs of other devices in the topology.

        Args:
            testbed_path (str): Path to the testbed YAML file.
            ubuntu_device_name (str): Name of the Ubuntu device to exclude from route generation.

        Returns:
            dict: A dictionary of routes in the format {'route-1': '192.168.x.x/24', ...}
        """
        tb = loader.load(testbed_path)
        route_set = set()

        for device_name, device in tb.devices.items():
            if device_name == ubuntu_device_name:
                continue

            # Collect routes from each device's interfaces
            for iface_name, iface in device.interfaces.items():
                if hasattr(iface, 'ipv4') and iface.ipv4:
                    network: IPv4Network = iface.ipv4.network
                    if network.prefixlen == 24:
                        route_set.add(str(network))

            # Include statically defined routes in 'custom.static_routes'
            static_routes = getattr(device.custom, "static_routes", [])
            for route in static_routes:
                net = IPv4Network(route["dest"])
                if net.prefixlen == 24:
                    route_set.add(str(net))

            # Include the FTD's management interface subnet if applicable
            if device.os == 'ftd' and 'mgmt' in device.interfaces:
                mgmt_iface = device.interfaces['mgmt']
                if hasattr(mgmt_iface, 'ipv4') and mgmt_iface.ipv4:
                    network: IPv4Network = mgmt_iface.ipv4.network
                    if network.prefixlen == 24:
                        route_set.add(str(network))

        # Convert to dictionary format
        route_dict = {f"route-{i + 1}": subnet for i, subnet in enumerate(sorted(route_set))}
        print(route_dict)
        return route_dict
