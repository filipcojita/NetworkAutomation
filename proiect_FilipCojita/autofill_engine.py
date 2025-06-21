"""
Autofill engine for pyATS testbed devices.

This module provides utility functions to automatically populate missing
attributes for devices in a pyATS testbed, such as hostname, credentials,
SSH/Telnet connection parameters, and static gateway routes.

Author: [Cojita Filip](https://github.com/filipcojita)
"""

from pyats.datastructures import AttrDict
import ipaddress

def compute_default_gateway(dev):
    """
    Compute the default gateway IP address for a device based on its initial interface link.

    This function inspects the link connected to the device's 'initial' interface and finds
    the IP address of a neighboring device on the same link.

    Args:
        dev: A pyATS Device object.

    Returns:
        str or None: The IP address of the neighbor device on the same link, or None if not found.
    """
    initial_iface = next((iface for iface in dev.interfaces.values() if iface.alias == 'initial'), None)
    if initial_iface and hasattr(initial_iface, 'link') and initial_iface.link:
        linked_devices = initial_iface.link.connected_devices
        for neighbor_dev in linked_devices:
            if neighbor_dev.name != dev.name:
                for neighbor_iface in neighbor_dev.interfaces.values():
                    if neighbor_iface.link == initial_iface.link:
                        return neighbor_iface.ipv4.ip.compressed
    return None

def autofill_missing_data(tb):
    """
    Automatically fill in missing data for network devices in the testbed.

    This function sets sensible defaults for devices that are not Linux or FTD, such as:
    - Default hostname if missing.
    - Default SSH and enable credentials if missing.
    - SSH connection details based on initial interface IP.
    - Fallback Telnet IP if undefined.
    - Default gateway based on topology.

    Args:
        tb: A pyATS testbed object (loaded with `loader.load()`).
    """
    for dev in tb.devices.values():
        # Skip Linux and FTD devices (handled differently)
        if dev.os in ['linux', 'ftd']:
            continue

        # Ensure `custom` section is present and is AttrDict
        if not isinstance(dev.custom, AttrDict):
            dev.custom = AttrDict(dev.custom)

        # Set default hostname based on device name
        if not hasattr(dev.custom, 'hostname'):
            dev.custom.hostname = dev.name

        if not hasattr(dev, 'credentials') or not dev.credentials:
            dev.credentials = AttrDict()

        # always check for 'default', even if 'credentials' exists
        if not hasattr(dev.credentials, 'default'):
            dev.credentials.default = AttrDict()
            dev.credentials.default.username = 'admin'
            dev.credentials.default.password = AttrDict()
            dev.credentials.default.password.plaintext = 'Admin123'

        # always ensure 'enable' exists
        if not hasattr(dev.credentials, 'enable'):
            dev.credentials.enable = AttrDict()
            dev.credentials.enable.password = AttrDict()
            dev.credentials.enable.password.plaintext = 'enablepa55'

        # If SSH connection missing, infer from initial interface
        if 'ssh' not in dev.connections and hasattr(dev, 'interfaces') and dev.interfaces:
            initial_iface = next((iface for iface in dev.interfaces.values() if iface.alias == 'initial'), None)
            if initial_iface:
                dev.connections.ssh = AttrDict()
                dev.connections.ssh.ip = initial_iface.ipv4.ip
                dev.connections.ssh.port = 22

        # Fallback for telnet IP (used by GNS3 or mock environments)
        if hasattr(dev.connections, 'telnet') and not hasattr(dev.connections.telnet, 'ip'):
            dev.connections.telnet.ip = ipaddress.ip_address('192.168.0.100')

        # Compute and set a default static gateway route if missing
        if not hasattr(dev.custom, 'gateway'):
            next_hop_ip = compute_default_gateway(dev)
            if next_hop_ip:
                dev.custom.gateway = {
                    'dest': '192.168.11.0',  # UbuntuServer address
                    'mask': '255.255.255.0',
                    'next_hop': next_hop_ip
                }
