"""
telnetconnector2 file to manage telnet connections,
depending on which device connects via telnet.
"""


import telnetlib
from time import sleep
from typing import Optional, Any, List
from pyats.datastructures import AttrDict
from pyats.topology import Device

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

    def execute(self, command: str, **kwargs: Any) -> str:
        """
        Execute a command over telnet and wait for prompt(s).
        """
        if not self._conn:
            raise RuntimeError("Connection not established. Call connect() first.")
        prompt: List[bytes] = list(map(lambda _: _.encode(), kwargs.get('prompt', [])))
        self._conn.write(f'{command}\n'.encode())
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
        if self.device.os == 'ios':
            self._initial_conf_ios()
        elif self.device.os == 'iosxe':
            self._initial_conf_csr()
        elif self.device.os == 'ftd':
            self._initial_conf_ftd()

    def _initial_conf_ios(self) -> None:
        """
        Initial configuration for IOS devices.
        """
        # self.execute('', prompt=['Would you like to enter the
        # initial configuration dialog? \\[yes/no\\]:'])
        # self.execute('no', prompt=['Would you like to terminate autoinstall?
        # \\[yes/no\\]:'])
        # self.execute('yes', prompt=['\\(Config Wizard\\)'])

        self.execute("\n", prompt=r'>')
        self.execute("en", prompt=r'#')
        self.execute('conf t', prompt=[r'\(config.*\)#'])

        interface = self.device.interfaces['initial']
        self.execute(f"int {interface.name}", prompt=[r'\(config-if\)#'])
        ip = interface.ipv4.ip.compressed
        mask = interface.ipv4.network.netmask.exploded
        self.execute(f"ip add {ip} {mask}", prompt=[r'\(config-if\)#'])
        self.execute('no shut', prompt=[r'\(config-if\)#'])
        self.execute('exit', prompt=[r'\(config\)#'])

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

        self.execute(f'username {username} privilege 15 secret {password}',
                     prompt=[r'\(config\)#'])
        self.execute('line vty 0 4', prompt=[r'\(config-line\)#'])
        self.execute("transport input ssh", prompt=[r'\(config-line\)#'])
        self.execute("login local", prompt=[r'\(config-line\)#'])
        self.execute('exit', prompt=[r'\(config\)#'])
        self.execute('ip ssh version 2', prompt=[r'\(config\)#'])
        self.execute('ip scp server enable', prompt=[r'\(config\)#'])

        enable_password = getattr(self.device.credentials, "enable", None)

        if enable_password and self.device.platform == 'iosv':
            self.execute(f'enable secret {enable_password.password.plaintext}',
                         prompt=[r'\(config\)#'])
            self.execute(
                f'ip route {self.device.custom.gateway["dest"]} {mask} {self.device.custom.gateway["next_hop"]}',
                prompt=[r'\(config\)#'])

        self.execute('end', prompt=[rf'{hostname}#'])
        self.execute('write memory', prompt=[rf'\[OK\]|{hostname}#'])
        self.execute('', prompt=[rf'{hostname}#'])

    def _initial_conf_csr(self) -> None:
        """
        Initial configuration for IOS-XE (CSR) devices.
        """
        # self.execute('', prompt=['Would you like to enter the
        # initial configuration dialog? \\[yes/no\\]:'])
        # self.execute('no', prompt=['Would you like to
        # terminate autoinstall? \\[yes/no\\]:'])
        # self.execute('yes', prompt=['enabled by Smart Agent for Licensing.\\'])

        self.execute("\n", prompt=r'>')
        self.execute('enable', prompt=[r'#'])
        self.execute('conf t', prompt=[r'\(config\)#'])

        interface = self.device.interfaces['initial']
        self.execute(f"int {interface.name}", prompt=[r'\(config-if\)#'])
        ip = interface.ipv4.ip.compressed
        mask = interface.ipv4.network.netmask.exploded
        self.execute(f"ip add {ip} {mask}", prompt=[r'\(config-if\)#'])
        self.execute('no shut', prompt=[r'\(config-if\)#'])
        self.execute('exit', prompt=[r'\(config\)#'])
        self.execute(f'ip route {self.device.custom.gateway["dest"]} {mask} {self.device.custom.gateway["next_hop"]}',
                     prompt=[r'\(config\)#'])

        hostname = self.device.custom.hostname
        self.execute(f'hostname {hostname}', prompt=[r'\(config\)#'])
        self.execute('ip domain name localdomain', prompt=[r'\(config\)#'])
        out = self.execute('crypto key generate rsa modulus 2048',
                           prompt=[r'\(config\)#', r'replace them\?'])
        sleep(5)
        if 'replace them' in out:
            self.execute('yes', prompt=[r'\(config\)#'])
            sleep(5)

        username = self.device.credentials.default['username']
        login_pass = self.device.credentials.default['password'].plaintext
        self.execute(f'username {username} privilege 15 secret {login_pass}',
                     prompt=[r'\(config\)#'])
        self.execute('line vty 0 4', prompt=[r'\(config-line\)#'])
        self.execute('transport input ssh', prompt=[r'\(config-line\)#'])
        self.execute('login local', prompt=[r'\(config-line\)#'])
        self.execute('exit', prompt=[r'\(config\)#'])
        self.execute('ip ssh version 2', prompt=[r'\(config\)#'])
        self.execute('ip scp server enable', prompt=[r'\(config\)#'])

        if "dhcp" in self.device.custom:
            for pool in self.device.custom["dhcp"]:
                self.execute(f"ip dhcp excluded-address {pool['excluded'][0]} {pool['excluded'][1]}",
                             prompt=[r'\(config\)#'])
                pool_name = f"POOL_{pool['network'].replace('.', '_')}"
                self.execute(f"ip dhcp pool {pool_name}", prompt=[r'\(dhcp-config\)#'])
                self.execute(f"network {pool['network']} {pool['mask']}", prompt=[r'\(dhcp-config\)#'])
                self.execute(f"default-router {pool['default_router']}", prompt=[r'\(dhcp-config\)#'])
                self.execute(f"dns-server {pool['dns_server']}", prompt=[r'\(dhcp-config\)#'])

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
