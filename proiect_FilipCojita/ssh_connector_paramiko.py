"""
ssh_connector_paramiko is the ssh connector file used by devices
in topology in order for ip interfaces and route configurations
to be done via ssh
"""

import re
import time
import logging
from time import sleep
from typing import Optional, List, Union
import paramiko
from pyats.datastructures import AttrDict
from pyats.topology import Device
import ipaddress

logger = logging.getLogger(__name__)

# Disable propagation to prevent pyATS from double-logging
logger.propagate = False

# Configure only if no handlers exist (prevent duplicates)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('> %(message)s'))  # Simple arrow prefix
    logger.addHandler(handler)

class SSHConnectorParamiko:
    DEFAULT_PROMPT: str = r'[>#]'

    def __init__(self, device: Device, **kwargs) -> None:
        """
        Initialize the SSH connector with a pyATS Device.

        Args:
            device (Device): pyATS device object to connect to.
            **kwargs: Optional parameters like timeout and buffer_size.
        """
        self.device: Device = device
        self.client: Optional[paramiko.SSHClient] = None
        self.shell: Optional[paramiko.Channel] = None
        self._connected: bool = False
        self.timeout: int = kwargs.get('timeout', 10)  # seconds for read/wait
        self._buffer_size: int = kwargs.get('buffer_size', 4096)

    def connect(self, **kwargs) -> None:
        """
        Establish an SSH connection and open an interactive shell.

        Raises:
            ValueError: If connection info is missing.
            RuntimeError: If connection or shell invocation fails.
        """
        connection: Optional[AttrDict] = kwargs.get('connection') or self.device.connections.ssh
        if not connection:
            raise ValueError("Missing connection information.")

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ip: str = connection.ip.compressed
        port: int = connection.port or 22
        username: str = self.device.credentials.default.username
        password: str = self.device.credentials.default.password.plaintext

        try:
            self.client.connect(
                hostname=ip,
                port=port,
                username=username,
                password=password,
                look_for_keys=False,
                allow_agent=False,
                timeout=10,
            )
            self.shell = self.client.invoke_shell()
            self.shell.settimeout(2)
            self._connected = True
            self._clear_buffer()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to {ip}:{port} - {e}")

    def _clear_buffer(self) -> None:
        """Flush any initial data in the shell buffer."""
        time.sleep(0.5)
        while self.shell and self.shell.recv_ready():
            self.shell.recv(self._buffer_size)
            time.sleep(0.1)

    def is_connected(self) -> bool:
        """
        Check if the SSH connection is active.

        Returns:
            bool: True if connected, False otherwise.
        """
        if self.client is None:
            return False
        transport = self.client.get_transport()
        return transport is not None and transport.is_active()

    def disconnect(self) -> None:
        """Close the SSH shell and client connections."""
        self.execute('write', prompt=r'#')
        sleep(3)

        if self.shell:
            self.shell.close()
        if self.client:
            self.client.close()
        self._connected = False

    def _read_until_prompt(self, prompt_patterns: Union[str, List[str]], timeout: Optional[int] = None) -> str:
        """
        Read from shell until a prompt pattern is matched or timeout occurs.

        Args:
            prompt_patterns (Union[str, List[str]]): Prompt regex or list of regex strings.
            timeout (Optional[int]): Timeout in seconds.

        Returns:
            str: The output read from the shell.

        Raises:
            TimeoutError: If prompt is not detected within timeout.
            RuntimeError: On read errors.
        """
        if isinstance(prompt_patterns, str):
            prompt_patterns = [prompt_patterns]

        prompt_regexes = [re.compile(p.encode()) for p in prompt_patterns]
        buffer = b''
        timeout = timeout or self.timeout
        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                if self.shell and self.shell.recv_ready():
                    chunk = self.shell.recv(self._buffer_size)
                    buffer += chunk

                    for regex in prompt_regexes:
                        if regex.search(buffer):
                            return buffer.decode(errors='ignore')
                else:
                    time.sleep(0.2)
            except Exception as e:
                raise RuntimeError(f"Error reading from shell: {e}")

        raise TimeoutError(f"Timeout waiting for prompt(s) {prompt_patterns}. Output so far:\n{buffer.decode(errors='ignore')}")

    def execute(self, command: str, prompt: Optional[Union[str, List[str]]] = None, timeout: Optional[int] = None) -> str:
        """
        Execute a command on the remote device and wait for prompt.

        Args:
            command (str): Command string to send.
            prompt (Optional[Union[str, List[str]]]): Expected prompt(s) regex.
            timeout (Optional[int]): Timeout for waiting prompt.

        Returns:
            str: Command output.

        Raises:
            RuntimeError: If connection not established or on command errors.
        """
        if not self._connected or not self.shell:
            raise RuntimeError("SSH connection is not established. Call connect() first.")

        prompt = prompt or self.DEFAULT_PROMPT

        logger.info(command)

        try:
            self.shell.send(f"{command}\n".encode())
            output = self._read_until_prompt(prompt, timeout)
            return output
        except TimeoutError as e:
            raise RuntimeError(f"Timeout executing command '{command}': {e}")
        except Exception as e:
            raise RuntimeError(f"Error executing command '{command}': {e}")

    def configure_routing(self) -> None:
        self.execute('configure terminal', prompt=r'\(config\)#')

        if hasattr(self.device.custom, 'static_routes') and self.device.custom.static_routes:
            for route in self.device.custom.static_routes:
                dest = route['dest']
                mask = route['mask']
                next_hop = route['next_hop']
                self.execute(f"ip route {dest} {mask} {next_hop}", prompt=r'\(config\)#')
            self.execute('end', prompt=r'#')
        else:
            area = getattr(self.device.custom, 'ospf_area', 0)
            self.execute(f'router ospf 1', prompt=r'\(config-router\)#')

            for iface in self.device.interfaces.values():
                network = iface.ipv4.network.network_address
                netmask = iface.ipv4.network.netmask
                wildcard = ipaddress.IPv4Address((2 ** 32 - 1) - int(netmask))

                self.execute(f'network {network} {wildcard} area {area}', prompt=r'\(config-router\)#')

            self.execute('end', prompt=r'#')

    def configure_interfaces(self) -> None:
        """
        Configure interfaces on the device based on the device's interface attributes.
        This function assumes each interface has 'name' and IPv4 info.

        If ip_helper section is found in custom section from testbed, then it will be added
        according to the provided parameters.
        """
        self.execute('configure terminal', prompt=r'\(config\)#')
        for iface in self.device.interfaces.values():
            if getattr(iface, 'alias', None) == 'initial':
                continue
            self.execute(f"interface {iface.name}", prompt=r'\(config-if\)#')
            ip = iface.ipv4.ip.compressed
            mask = iface.ipv4.network.netmask.exploded
            self.execute(f"ip address {ip} {mask}", prompt=r'\(config-if\)#')
            self.execute('no shutdown', prompt=r'\(config-if\)#')
            self.execute('exit', prompt=r'\(config\)#')

        # ip-helper condition
        if 'ip_helper' in self.device.custom:
            for iface_name, iface in self.device.interfaces.items():
                # Check if the interface's alias matches the next_hop
                if hasattr(iface, 'alias') and iface.alias == self.device.custom['ip_helper']['next_hop']:
                    self.execute(f'interface {iface_name}', prompt=r'\(config-if\)#')
                    self.execute(f'ip helper-address {self.device.custom["ip_helper"]["ip"]}',
                                 prompt=r'\(config-if\)#')
                    self.execute('exit', prompt=r'\(config\)#')

        self.execute('end', prompt=r'#')

    def configure_dhcp(self) -> None:
        # configure dhcp for csr device (or for any devices that specify dhcp in testbed)
        if "dhcp" in self.device.custom:
            self.execute("configure terminal", prompt=r'\(config\)#')
            for pool in self.device.custom["dhcp"]:
                self.execute(f"ip dhcp excluded-address {pool['excluded'][0]} {pool['excluded'][1]}",
                             prompt=[r'\(config\)#'])
                pool_name = f"POOL_{pool['network'].replace('.', '_')}"
                self.execute(f"ip dhcp pool {pool_name}", prompt=[r'\(dhcp-config\)#'])
                self.execute(f"network {pool['network']} {pool['mask']}", prompt=[r'\(dhcp-config\)#'])
                self.execute(f"default-router {pool['default_router']}", prompt=[r'\(dhcp-config\)#'])
                self.execute(f"dns-server {pool['dns_server']}", prompt=[r'\(dhcp-config\)#'])
            self.execute("exit", prompt=r'#')