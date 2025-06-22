"""
5 tests using unittest library and MagicMock for the network automation project.

This suite covers:
- SSH and Telnet command execution via connectors
- Interface attribute validation
- Route duplication detection on Ubuntu devices
- Behavior of the autofill engine
- Execution timeout handling in SSHConnectorParamiko
"""

import unittest
from unittest.mock import patch, MagicMock
from ipaddress import ip_address
from pyats.datastructures import AttrDict
from pyats.topology import Device, Testbed, Interface
from autofill_engine import autofill_missing_data
from ubuntu_setup import UbuntuNetworkConfigurator
from ssh_connector_paramiko import SSHConnectorParamiko
from telnet_connector2 import TelnetConnector2


class TestUbuntuConfiguratorRouteDuplication(unittest.TestCase):
    """
    Test that UbuntuNetworkConfigurator.configure() avoids re-adding routes
    that already exist on the system.
    """

    @patch('ubuntu_setup.subprocess.run')
    def test_skips_duplicate_routes(self, mock_run):
        """
        Simulate detection of an existing route and ensure that
        'ip route add' is NOT called for it.
        """
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "192.168.99.0/24 via 192.168.1.1 dev eth0"

        dev = Device(name="UbuntuHost")
        dev.custom = {
            'network_config': {
                'interface': 'eth0',
                'ip': '192.168.1.10/24',
                'gateway': '192.168.1.1',
                'routes': {
                    'dup': '192.168.99.0/24'
                }
            }
        }

        configurator = UbuntuNetworkConfigurator(dev)

        with patch.object(configurator, 'route_exists', return_value=True) as mock_check:
            configurator.configure()

        for call_args in mock_run.call_args_list:
            if 'ip route add' in ' '.join(call_args[0][0]):
                self.fail("Duplicate route was incorrectly added via subprocess")

        mock_check.assert_called_once_with('192.168.99.0/24')


class TestSSHConnectorParamiko(unittest.TestCase):
    """
    Unit tests for the SSHConnectorParamiko class.

    Verifies SSH command execution, shell prompt detection, and connection setup.
    """

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_ssh_connect_and_execute(self, mock_ssh_client):
        """
        Simulates a valid SSH shell session and tests that
        commands are sent and prompt-matching output is returned.
        """
        mock_client = mock_ssh_client.return_value
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell

        def side_effect_recv_ready():
            side_effect_recv_ready.calls += 1
            return side_effect_recv_ready.calls == 1
        side_effect_recv_ready.calls = 0

        mock_shell.recv_ready.side_effect = side_effect_recv_ready
        mock_shell.recv.return_value = b'test prompt#'

        device = Device(
            name='test-device',
            connections={'ssh': {'ip': '192.0.2.1'}},
            credentials={'default': {'username': 'user', 'password': 'pass'}}
        )

        connector = SSHConnectorParamiko(device)
        connector.client = mock_client
        connector.shell = mock_shell
        connector._connected = True

        output = connector.execute('show version', prompt='#')
        self.assertIn('test prompt#', output)
        mock_shell.send.assert_called_with(b'show version\n')


class TestTelnetConnector2(unittest.TestCase):
    """
    Unit tests for the TelnetConnector2 class.

    Validates Telnet connection, command execution, and disconnection.
    """

    @patch('telnet_connector2.telnetlib.Telnet')
    def test_telnet_connect_and_execute(self, mock_telnet):
        """
        Simulates a Telnet session: verifies connection setup,
        command execution, prompt reading, and connection teardown.
        """
        device = Device(
            name='test-device',
            connections={
                'telnet': {
                    'ip': ip_address('192.0.2.2'),
                    'port': 23
                }
            },
            credentials={
                'default': {
                    'username': 'admin',
                    'password': {'plaintext': 'pass123'}
                }
            }
        )

        connector = TelnetConnector2(device)
        mock_conn_instance = MagicMock()
        mock_telnet.return_value = mock_conn_instance

        connector.connect(connection=device.connections.telnet)
        mock_telnet.assert_called_once_with(host='192.0.2.2', port=23, timeout=10)

        mock_conn_instance.expect.return_value = (0, None, b"output text")
        output = connector.execute('show version', prompt=[r'#'])
        mock_conn_instance.write.assert_called_once_with(b'show version\n')
        self.assertEqual(output, "output text")

        mock_conn_instance.eof = False
        self.assertTrue(connector.is_connected())

        connector.disconnect()
        mock_conn_instance.close.assert_called_once()


def interface_has_required_params(interface):
    """
    Utility function to validate that an interface has essential
    attributes: type, link, and a valid IPv4 address.
    """
    return all([
        hasattr(interface, 'type') and interface.type,
        hasattr(interface, 'link') and interface.link,
        hasattr(interface, 'ipv4') and interface.ipv4 and hasattr(interface.ipv4, 'ip')
    ])


class TestInterfaceParameters(unittest.TestCase):
    """
    Tests to ensure interfaces are valid and complete for automation.
    """

    def test_interface_has_all_required_parameters(self):
        iface = MagicMock()
        iface.name = "GigabitEthernet0/1"
        iface.type = "ethernet"
        iface.link = MagicMock()
        iface.ipv4 = MagicMock()
        iface.ipv4.ip = "192.168.1.1"

        self.assertTrue(interface_has_required_params(iface))

    def test_interface_missing_type(self):
        iface = MagicMock()
        iface.name = "GigabitEthernet0/1"
        iface.type = None
        iface.link = MagicMock()
        iface.ipv4 = MagicMock()
        iface.ipv4.ip = "192.168.1.1"
        self.assertFalse(interface_has_required_params(iface))

    def test_interface_missing_link(self):
        iface = MagicMock()
        iface.name = "GigabitEthernet0/1"
        iface.type = "ethernet"
        iface.link = None
        iface.ipv4 = MagicMock()
        iface.ipv4.ip = "192.168.1.1"
        self.assertFalse(interface_has_required_params(iface))

    def test_interface_missing_ipv4(self):
        iface = MagicMock()
        iface.name = "GigabitEthernet0/1"
        iface.type = "ethernet"
        iface.link = MagicMock()
        iface.ipv4 = None
        self.assertFalse(interface_has_required_params(iface))


class TestSSHExecuteMethod(unittest.TestCase):
    """
    Unit tests for the SSHConnectorParamiko.execute() method,
    including timeout behavior and command output capture.
    """

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_execute_returns_output(self, mock_ssh_client):
        mock_client = mock_ssh_client.return_value
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell

        mock_shell.recv_ready.side_effect = [True]
        mock_shell.recv.return_value = b"hostname#"

        device = Device(name="TestRouter")
        device.connections = {'ssh': {'ip': '192.168.0.1', 'port': 22}}
        device.credentials = {
            'default': {
                'username': 'admin',
                'password': {'plaintext': 'Admin123'}
            }
        }

        connector = SSHConnectorParamiko(device)
        connector.client = mock_client
        connector.shell = mock_shell
        connector._connected = True

        output = connector.execute("show version", prompt="#")
        mock_shell.send.assert_called_with(b"show version\n")
        self.assertIn("hostname#", output)

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_execute_raises_on_not_connected(self, mock_ssh_client):
        """
        Verifies that execute() raises RuntimeError when
        the SSH session is not connected.
        """
        device = Device(name="TestRouter")
        connector = SSHConnectorParamiko(device)
        connector._connected = False
        connector.shell = None

        with self.assertRaises(RuntimeError) as cm:
            connector.execute("show version")

        self.assertIn("SSH connection is not established", str(cm.exception))

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_execute_raises_timeout_error(self, mock_ssh_client):
        """
        Simulates a shell that never returns a prompt, triggering a timeout.
        """
        mock_client = mock_ssh_client.return_value
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell

        mock_shell.recv_ready.return_value = False

        device = Device(name="TimeoutDevice")
        device.connections = {'ssh': {'ip': '192.168.0.1', 'port': 22}}
        device.credentials = {
            'default': {
                'username': 'admin',
                'password': {'plaintext': 'Admin123'}
            }
        }

        connector = SSHConnectorParamiko(device, timeout=1)
        connector.client = mock_client
        connector.shell = mock_shell
        connector._connected = True

        with self.assertRaises(RuntimeError) as cm:
            connector.execute("show running-config", prompt="#")

        self.assertIn("Timeout executing command", str(cm.exception))


class TestAutofillMissingData(unittest.TestCase):
    """
    Unit test for autofill_missing_data(). Ensures that missing device
    attributes are automatically completed.
    """

    def setUp(self):
        self.tb = Testbed(name='mock-testbed')
        self.tb.devices = {}

        dev = Device(name="Router1", os="ios", testbed=self.tb)
        dev.custom = AttrDict()
        dev.connections = AttrDict()
        dev.interfaces = {}

        iface = Interface(name="GigabitEthernet0/0", type='ethernet', ipv4='', link='', alias='')
        iface.alias = "initial"
        iface.ipv4 = MagicMock()
        iface.ipv4.ip.compressed = "192.168.1.1"
        iface.ipv4.network.netmask.exploded = "255.255.255.0"
        iface.link = MagicMock()
        iface.link.connected_devices = [dev]
        dev.interfaces["GigabitEthernet0/0"] = iface

        neighbor = Device(name="Router2", os="ios")
        neighbor.interfaces = {}
        neighbor_iface = Interface(name="GigabitEthernet0/1", type='ethernet', ipv4='', link='', alias='')
        neighbor_iface.ipv4 = MagicMock()
        neighbor_iface.ipv4.ip.compressed = "192.168.1.254"
        neighbor_iface.link = iface.link
        neighbor.interfaces["GigabitEthernet0/1"] = neighbor_iface
        iface.link.connected_devices.append(neighbor)

        self.tb.devices["Router1"] = dev
        self.tb.devices["Router2"] = neighbor

    def test_autofill_completes_required_fields(self):
        """
        Verifies that autofill_missing_data correctly fills hostname, credentials,
        SSH connection info, and static gateway.
        """
        autofill_missing_data(self.tb)
        dev = self.tb.devices["Router1"]

        self.assertEqual(dev.custom.hostname, "Router1")
        self.assertEqual(dev.credentials.default.username, "admin")
        self.assertEqual(dev.credentials.default.password.plaintext, "Admin123")
        self.assertEqual(dev.credentials.enable.password.plaintext, "enablepa55")
        self.assertIn("ssh", dev.connections)
        self.assertEqual(dev.connections.ssh.port, 22)
        self.assertEqual(dev.connections.ssh.ip, dev.interfaces["GigabitEthernet0/0"].ipv4.ip)
        self.assertIn("gateway", dev.custom)
        self.assertEqual(dev.custom.gateway["next_hop"], "192.168.1.254")


if __name__ == '__main__':
    unittest.main()
