import logging
import subprocess
from pyats.topology import Device

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, encoding='utf-8')


class UbuntuNetworkConfigurator:
    """
    Configure Ubuntu network interface and static routes using a PyATS Device object.
    """

    def __init__(self, device: Device):
        """
        Initialize configurator with Device object loaded from PyATS testbed.
        """
        self.device = device
        self.name = device.name
        custom = device.custom.get('network_config', {})

        self.interface = custom.get('interface')
        self.ip = custom.get('ip')
        self.gateway = custom.get('gateway')
        self.routes = custom.get('routes', {})

        if not all([self.interface, self.ip, self.gateway]):
            raise ValueError(f"Missing required config values for {self.name}")

    def run_command(self, cmd):
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"Error: {result.stderr.strip()}")
        else:
            logger.debug(f"Output: {result.stdout.strip()}")

    def configure(self):
        self.run_command(['sudo', 'ip', 'address', 'add', self.ip, 'dev', self.interface])
        self.run_command(['sudo', 'ip', 'link', 'set', self.interface, 'up'])

        for label, subnet in self.routes.items():
            self.run_command(['sudo', 'ip', 'route', 'add', subnet, 'via', self.gateway])

        logger.info(f"Finished configuration for Ubuntu device: {self.name}")
