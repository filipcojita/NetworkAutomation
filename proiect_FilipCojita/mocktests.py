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
    Verifies that UbuntuNetworkConfigurator does not re-add static routes
    that already exist in the system.
    """

    @patch('ubuntu_setup.subprocess.run')
    def test_skips_duplicate_routes(self, mock_run):
        """
        Mocks subprocess.run() to simulate a route that already exists.
        Ensures 'ip route add' is not executed again.
        """
        # simulate command output that indicates route already exists
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "192.168.99.0/24 via 192.168.1.1 dev eth0"

        # define fake Ubuntu dev with duplicate route
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

        # instantiate configurator
        configurator = UbuntuNetworkConfigurator(dev)

        # patch route_exists() method to simulate route is present
        with patch.object(configurator, 'route_exists', return_value=True) as mock_check:
            configurator.configure()

        # assert 'ip route add' was not called for duplicate route
        for call_args in mock_run.call_args_list:
            if 'ip route add' in ' '.join(call_args[0][0]):
                self.fail("Duplicate route was incorrectly added via subprocess")

        # check that route_exists was called exactly once
        mock_check.assert_called_once_with('192.168.99.0/24')


class TestSSHConnectorParamiko(unittest.TestCase):
    """
    Unit test for SSHConnectorParamiko.
    Validates sending a command and reading its result via mocked SSH session.
    """

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_ssh_connect_and_execute(self, mock_ssh_client):
        """
        Simulates SSH connection and ensures command is sent and output is received.
        """
        # create mock SSH shell
        mock_client = mock_ssh_client.return_value
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell

        # configure shell to simulate that it has data ready 1-TIME-ONLY
        def side_effect_recv_ready():
            side_effect_recv_ready.calls += 1
            return side_effect_recv_ready.calls == 1
        side_effect_recv_ready.calls = 0

        mock_shell.recv_ready.side_effect = side_effect_recv_ready
        mock_shell.recv.return_value = b'test prompt#'

        # define test device
        device = Device(
            name='test-device',
            connections={'ssh': {'ip': '192.0.2.1'}},
            credentials={'default': {'username': 'user', 'password': 'pass'}}
        )

        # inject mocked client and shell into connector
        connector = SSHConnectorParamiko(device)
        connector.client = mock_client
        connector.shell = mock_shell
        connector._connected = True

        # execute a command and validate result
        output = connector.execute('show version', prompt='#')
        self.assertIn('test prompt#', output)
        mock_shell.send.assert_called_with(b'show version\n')


class TestTelnetConnector2(unittest.TestCase):
    """
    Unit test for TelnetConnector2.
    Verifies that commands are correctly sent and responses are captured.
    """

    @patch('telnet_connector2.telnetlib.Telnet')
    def test_telnet_connect_and_execute(self, mock_telnet):
        """
        Simulates a Telnet session with connect/execute/disconnect flow.
        """
        # define fake device
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

        # simulate Telnet session
        mock_conn_instance = MagicMock()
        mock_telnet.return_value = mock_conn_instance

        # test connection
        connector.connect(connection=device.connections.telnet)
        mock_telnet.assert_called_once_with(host='192.0.2.2', port=23, timeout=10)

        # test command execution and prompt reading
        mock_conn_instance.expect.return_value = (0, None, b"output text")
        output = connector.execute('show version', prompt=[r'#'])
        mock_conn_instance.write.assert_called_once_with(b'show version\n')
        self.assertEqual(output, "output text")

        # test connection status
        mock_conn_instance.eof = False
        self.assertTrue(connector.is_connected())

        # test disconnection
        connector.disconnect()
        mock_conn_instance.close.assert_called_once()


class TestSSHExecuteMethod(unittest.TestCase):
    """
    Tests for SSHConnectorParamiko.execute():
    - Normal execution
    - Not connected case
    - Timeout behavior
    """

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_execute_returns_output(self, mock_ssh_client):
        # simulate receiving expected output
        mock_client = mock_ssh_client.return_value
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell
        mock_shell.recv_ready.side_effect = [True]
        mock_shell.recv.return_value = b"hostname#"

        # dev mock
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

        # validate output and command sent
        output = connector.execute("show version", prompt="#")
        mock_shell.send.assert_called_with(b"show version\n")
        self.assertIn("hostname#", output)

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_execute_raises_on_not_connected(self, mock_ssh_client):
        """
        Ensure that RuntimeError is raised if SSH is not connected.
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
        Simulates no prompt being received, which should trigger timeout.
        """
        mock_client = mock_ssh_client.return_value
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell
        mock_shell.recv_ready.return_value = False  # no data ready ever

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
    Test for autofill_missing_data(): ensures automatic completion of device attributes.
    """

    def setUp(self):
        """
        Create a mock testbed with two connected routers.
        """
        self.tb = Testbed(name='mock-testbed')
        self.tb.devices = {}

        # Router1 definition
        dev = Device(name="Router1", os="ios", testbed=self.tb)
        dev.custom = AttrDict()
        dev.connections = AttrDict()
        dev.interfaces = {}

        # interface on Router1
        iface = Interface(name="GigabitEthernet0/0", type='ethernet', ipv4='', link='', alias='')
        iface.alias = "initial"
        iface.ipv4 = MagicMock()
        iface.ipv4.ip.compressed = "192.168.1.1"
        iface.ipv4.network.netmask.exploded = "255.255.255.0"
        iface.link = MagicMock()
        iface.link.connected_devices = [dev]
        dev.interfaces["GigabitEthernet0/0"] = iface

        # neighbor Router2
        neighbor = Device(name="Router2", os="ios")
        neighbor.interfaces = {}
        neighbor_iface = Interface(name="GigabitEthernet0/1", type='ethernet', ipv4='', link='', alias='')
        neighbor_iface.ipv4 = MagicMock()
        neighbor_iface.ipv4.ip.compressed = "192.168.1.254"
        neighbor_iface.link = iface.link
        neighbor.interfaces["GigabitEthernet0/1"] = neighbor_iface
        iface.link.connected_devices.append(neighbor)

        # add devs to testbed
        self.tb.devices["Router1"] = dev
        self.tb.devices["Router2"] = neighbor

    def test_autofill_completes_required_fields(self):
        """
        Ensure that hostname, credentials, SSH config, and gateway are auto-completed.
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
