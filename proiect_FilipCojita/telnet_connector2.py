"""
telnetconnector2 file to manage telnet connections,
depending on which device connects via telnet.
"""
import logging
import telnetlib
from time import sleep
from typing import Optional, Any, List
from pyats.datastructures import AttrDict
from pyats.topology import Device
from unicon.plugins.asa.statements import enable_password

logger = logging.getLogger(__name__)

# Disable propagation to prevent pyATS from double-logging
logger.propagate = False

# Configure only if no handlers exist (prevent duplicates)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('> %(message)s'))  # Simple arrow prefix
    logger.addHandler(handler)

class TelnetConnector2:
    """
    Telnet connector class to manage telnet connections and device configuration.
    """

    def __init__(self, device: Device, **kwargs) -> None:
        """
        Initialize with a pyATS Device object.
        """
        self._conn: Optional[telnetlib.Telnet] = None
        self.device: Device = device
        self.connection: Optional[AttrDict] = None

    def connect(self, **kwargs: Any) -> None:
        """
        Establish a telnet connection using provided connection info.
        """
        self.connection = kwargs.get('connection')
        if not self.connection:
            raise ValueError("Missing connection information.")

        self._conn = telnetlib.Telnet(
            host=self.connection.ip.compressed,
            port=self.connection.port,
            timeout=10
        )

    def is_connected(self) -> bool:
        """
        Check if telnet connection is active.
        """
        return self._conn is not None and not self._conn.eof

    def disconnect(self) -> None:
        """
        Close the telnet connection if open.
        """
        if self._conn:
            self._conn.close()

    def write(self, command: str) -> None:
        """
        Sends a command to the device.
        """
        self._conn.write(command.encode() + b'\n')

    def read(self) -> str:
        """
        Performs a read_very_eager
        Return:
            The output of the read
        """
        return self._conn.read_very_eager().decode()

    def try_skip_initial_config_dialog(self, last_out: str):
        """
        Checks if autoconfiguration is in progress and cancels if so
            Args:
                last_out(str): The last output on the console
        """
        self.write('')
        if 'initial configuration dialog?' or '\'yes\' or \'no\'' in last_out:
            self.execute('no', prompt=[r'terminate autoinstall\? \[yes\]:'])
            self.write('yes')
            sleep(20)
            self.write('\r')
            self.execute('', prompt=[r'\w+\>'])

    def execute(self, command: str, **kwargs: Any) -> str:
        """
        Execute a command over telnet and wait for prompt(s).
        """
        if not self._conn:
            raise RuntimeError("Connection not established. Call connect() first.")
        prompt: List[bytes] = list(map(lambda _: _.encode(), kwargs.get('prompt', [])))
        self._conn.write(f'{command}\n'.encode())
        logger.info(command)
        try:
            index, match, output = self._conn.expect(prompt, timeout=10)
            return output.decode(errors="ignore")
        except EOFError:
            raise RuntimeError("Connection closed unexpectedly during command execution.")
        except Exception as e:
            raise RuntimeError(f"Error executing command '{command}': {e}")

    def do_initial_configuration(self) -> None:
        """
        Perform initial device configuration based on device OS.
        """
        if self.device.os in ['ios', 'iosxe']:
            self._initial_conf_router()
        elif self.device.os == 'ftd':
            self._initial_conf_ftd()

    def _initial_conf_router(self) -> None:
        """
        Perform initial configuration on Cisco IOS or IOS-XE routers.

        This method handles the essential first-time configuration steps for a router
        using Telnet. It is intended to bring the device into a manageable state
        with basic interface, routing, and SSH access settings. The actions include:

        - Entering privileged EXEC and global configuration mode.
        - Setting up the primary routed interface (marked 'initial' in the testbed):
            - Assigning IP address and subnet mask.
            - Bringing the interface up with 'no shutdown'.
        - Optionally configuring a static route if 'gateway' is defined under `device.custom`.
        - Setting hostname and domain name for crypto key generation.
        - Generating RSA keys for SSH access (replaces existing keys if needed).
        - Creating a local user with privilege 15 and encrypted password (from credentials).
        - Enabling SSH and SCP servers.
        - Enabling local login and SSH access on VTY lines.
        - Optionally configuring an 'enable secret' password (only if platform is 'iosv').

        Finally, the configuration is saved to NVRAM and the CLI is returned to exec mode.

        Notes:
            - This method assumes the `device` object is a valid pyATS Device with
              properly defined `interfaces`, `credentials`, and `custom` attributes.
            - For full automation, ensure `device.interfaces['initial']` exists.
            - SSH configuration assumes 'default' credential group contains username/password.

        Raises:
            RuntimeError: If any command execution fails or the connection is not active.
        """

        # skip initial dialog
        out = self.read()
        self.try_skip_initial_config_dialog(out)

        self.execute("\n", prompt=r'>')
        self.execute("en", prompt=r'#')
        self.execute('conf t', prompt=[r'\(config.*\)#'])

        # configure initial interface
        interface = self.device.interfaces['initial']
        self.execute(f"int {interface.name}", prompt=[r'\(config-if\)#'])
        ip = interface.ipv4.ip.compressed
        mask = interface.ipv4.network.netmask.exploded
        self.execute(f"ip add {ip} {mask}", prompt=[r'\(config-if\)#'])
        self.execute('no shut', prompt=[r'\(config-if\)#'])
        self.execute('exit', prompt=[r'\(config\)#'])

        # configure initial route
        if 'gateway' in self.device.custom:
            self.execute(
                f'ip route {self.device.custom.gateway["dest"]} {mask} {self.device.custom.gateway["next_hop"]}',
                prompt=[r'\(config\)#'])

        #configure ssh on device
        hostname = self.device.custom.hostname
        self.execute(f'hostname {hostname}', prompt=[r'\(config\)#'])
        self.execute('ip domain name localdomain', prompt=[r'\(config\)#'])
        out = self.execute('crypto key generate rsa modulus 2048',
                           prompt=[r'\(config\)#', r'replace them\?'])
        sleep(5)
        if 'replace them' in out:
            self.execute('yes', prompt=[r'\(config\)#'])
            sleep(5)
        username = self.device.credentials.default.username
        password = self.device.credentials.default.password.plaintext
        enable_password = self.device.credentials.enable.password.plaintext
        self.execute(f'username {username} privilege 15 secret {password}',
                     prompt=[r'\(config\)#'])
        self.execute('line vty 0 4', prompt=[r'\(config-line\)#'])
        self.execute("transport input ssh", prompt=[r'\(config-line\)#'])
        self.execute("login local", prompt=[r'\(config-line\)#'])
        self.execute('exit', prompt=[r'\(config\)#'])
        self.execute('ip ssh version 2', prompt=[r'\(config\)#'])
        self.execute('ip scp server enable', prompt=[r'\(config\)#'])
        self.execute(f'enable secret {enable_password}', prompt=[r'\(config\)#'])
        self.execute('end', prompt=[rf'{hostname}#'])
        self.execute('write memory', prompt=[rf'\[OK\]|{hostname}#'])
        self.execute('', prompt=[rf'{hostname}#'])

    def _initial_conf_ftd(self) -> None:
        """
        Initial configuration for Firepower Threat Defense (FTD) devices.
        """
        hostname = self.device.custom.hostname
        dns = self.device.custom.dns

        self.execute('', prompt=['firepower login:'])
        self.execute('admin', prompt=['Password:'])
        self.execute('Admin123', prompt=['Press <ENTER> to display the EULA:'])

        self.execute('\n', prompt=['--MORE--'])
        for i in range(15):
            self._conn.write(b' ')  # write space key
            sleep(0.5)

        self._conn.expect([b'AGREE to the EULA:'])
        self.execute('', prompt=['Enter new password:'])
        self.execute(f'{self.device.connections.ssh.credentials.login.password.plaintext}',
                     prompt=['Confirm new password:'])
        self.execute(f'{self.device.connections.ssh.credentials.login.password.plaintext}',
                     prompt=['Do you want to configure IPv4\\? \\(y/n\\) \\[y\\]:'])
        self.execute('y', prompt=['Do you want to configure IPv6\\? \\(y/n\\) \\[n\\]:'])
        self.execute('n', prompt=['Configure IPv4 via DHCP or manually\\? \\(dhcp/manual\\) \\[manual\\]:'])
        self.execute('manual', prompt=['Enter an IPv4 address for the management interface \\[192\\.168\\.45\\.45\\]:'])
        self.execute(self.device.interfaces['mgmt'].ipv4.ip.compressed,
                     prompt=['Enter an IPv4 netmask for the management interface \\[255\\.255\\.255\\.0\\]'])
        self.execute(self.device.interfaces['mgmt'].ipv4.netmask.compressed,
                     prompt=['Enter the IPv4 default gateway for the management interface \\[192\\.168\\.45\\.1\\]:'])
        self.execute(f'{self.__find_gateway_ftd()}',
                     prompt=['Enter a fully qualified hostname for this system \\[firepower\\]:'])
        self.execute(f'{hostname}', prompt=['Enter a comma-separated list of DNS severs or \'none\' \\[200\\.67\\.222\\.222\\,208\\.67\\.220\\.220\\]'])
        self.execute(f'{dns}', prompt=['Enter a comma-separated list of search domains or \'none\' \\[\\]'])
        self.execute('none', prompt=['Manage the device locally\\? \\(yes/no\\) \\[yes\\]:'])
        self.execute('yes', prompt=['>'])

    def enable_rest(self) -> None:
        """
        Enable REST API on the device.
        """
        self.execute('conf t', prompt=[r'\(config\)#'])
        self.execute("ip http secure-server", prompt=[r'\(config\)#'])
        self.execute("restconf", prompt=[r'\(config\)#'])

    def get_network_driver(self) -> None:
        """
        Placeholder for network driver retrieval (not implemented).
        """
        raise NotImplementedError("get_network_driver is not implemented yet.")

    def __find_gateway_ftd(self):
        """
        Find the gateway IP for FTD device from custom attributes.
        """
        link_obj = self.device.interfaces['mgmt'].link
        for dev in link_obj.connected_devices:
            if dev == self.device:
                continue
            for interface in dev.interfaces.values():
                int_found = interface if interface.link == link_obj else None
                if int_found:
                    return int_found.ipv4.ip.compressed
        return None
