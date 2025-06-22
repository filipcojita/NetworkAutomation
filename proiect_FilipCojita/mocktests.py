"""
5 tests using unittest library and MagicMock for the network automation project
"""

import subprocess
import unittest
from unittest.mock import patch, call, MagicMock
from ipaddress import ip_address
from pyats.topology import Device
from pyats.datastructures import AttrDict
from ubuntu_setup import UbuntuNetworkConfigurator
from ssh_connector_paramiko import SSHConnectorParamiko
from telnet_connector2 import TelnetConnector2

class TestUbuntuNetworkConfigurator(unittest.TestCase):
    """
    Unit tests for the UbuntuNetworkConfigurator class.
    These tests check that Ubuntu devices are configured correctly using subprocess commands.
    """

    @patch('ubuntu_setup.subprocess.run')
    def test_configure_applies_network_commands(self, mock_run):
        """
        Test that configure() method applies expected network commands:
        - Adds IP address to the interface.
        - Brings interface up.
        - Adds routes via specified gateway.
        """
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ''
        mock_run.return_value.stderr = ''

        dev = Device(name="UbuntuHost")
        dev.custom = AttrDict({
            'network_config': {
                'interface': 'eth0',
                'ip': '192.168.10.10/24',
                'gateway': '192.168.10.1',
                'routes': {
                    'r1': '192.168.20.0/24',
                    'r2': '192.168.30.0/24'
                }
            }
        })

        configurator = UbuntuNetworkConfigurator(dev)
        configurator.configure()

        # Expected subprocess calls
        expected_calls = [
            (['sudo', 'ip', 'address', 'add', '192.168.10.10/24', 'dev', 'eth0']),
            (['sudo', 'ip', 'link', 'set', 'eth0', 'up']),
            (['sudo', 'ip', 'route', 'add', '192.168.20.0/24', 'via', '192.168.10.1']),
            (['sudo', 'ip', 'route', 'add', '192.168.30.0/24', 'via', '192.168.10.1']),
        ]

        # Assert that subprocess.run was called with expected arguments
        for call_args in expected_calls:
            mock_run.assert_any_call(call_args, stdout=unittest.mock.ANY, stderr=unittest.mock.ANY, text=True)

    @patch('ubuntu_setup.subprocess.run')
    def test_run_command_logs_error_on_failure(self, mock_run):
        """
        Test that run_command() logs an error if a subprocess call fails.
        """
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = 'some error occurred'

        # Create an uninitialized configurator for isolated method testing
        configurator = UbuntuNetworkConfigurator.__new__(UbuntuNetworkConfigurator)

        with patch('ubuntu_setup.logger') as mock_logger:
            configurator.run_command(['fake', 'cmd'])

            # Ensure the error message is logged
            mock_logger.error.assert_called_with("Error: some error occurred")

    def test_init_raises_if_missing_config(self):
        """
        Test that __init__ raises ValueError when required network configuration is missing.
        Required keys: interface, ip, gateway.
        """
        dev = Device(name="BrokenUbuntu")
        dev.custom = AttrDict({
            'network_config': {
                'ip': '192.168.10.10/24',  # missing 'interface' and 'gateway'
            }
        })

        # Expect a ValueError due to incomplete config
        with self.assertRaises(ValueError) as context:
            UbuntuNetworkConfigurator(dev)

        self.assertIn("Missing required config values", str(context.exception))

class TestSSHConnectorParamiko(unittest.TestCase):
    """
    Unit tests for the SSHConnectorParamiko class.

    This test suite verifies that:
    - SSH connections are correctly established using Paramiko.
    - Shell commands are properly sent.
    - Prompt output is correctly received.
    """

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_ssh_connect_and_execute(self, mock_ssh_client):
        """
        Simulate an SSH connection and test command execution.

        Verifies that:
        - The `send()` method is called with the expected command.
        - The output from the simulated shell includes the expected prompt.
        """
        # Create mock SSH client and shell
        mock_client = mock_ssh_client.return_value
        mock_shell = MagicMock()
        mock_client.invoke_shell.return_value = mock_shell

        # Simulate `recv_ready()` returning True once
        def side_effect_recv_ready():
            side_effect_recv_ready.calls += 1
            return side_effect_recv_ready.calls == 1
        side_effect_recv_ready.calls = 0

        mock_shell.recv_ready.side_effect = side_effect_recv_ready
        mock_shell.recv.return_value = b'test prompt#'

        # Define a mock device with minimal connection data
        device = Device(
            name='test-device',
            connections={'ssh': {'ip': '192.0.2.1'}},
            credentials={'default': {'username': 'user', 'password': 'pass'}}
        )

        # Manually inject mocked client and shell into the connector
        connector = SSHConnectorParamiko(device)
        connector.client = mock_client
        connector.shell = mock_shell
        connector._connected = True

        # Run command and assert expected output
        output = connector.execute('show version', prompt='#')
        self.assertIn('test prompt#', output)

        # Ensure command was sent
        mock_shell.send.assert_called_with(b'show version\n')


class TestTelnetConnector2(unittest.TestCase):
    """
    Unit tests for the TelnetConnector2 class.

    This test suite validates:
    - Telnet connection setup using mocked IP and port.
    - Proper command execution and output reading.
    - Connection status checking and graceful disconnection.
    """

    @patch('telnet_connector2.telnetlib.Telnet')
    def test_telnet_connect_and_execute(self, mock_telnet):
        """
        Simulate a Telnet connection and test command execution.

        Verifies that:
        - The Telnet session is initialized with the right host and port.
        - Commands are written to the session.
        - The session correctly receives and decodes expected output.
        - Connection status and disconnect behavior work as expected.
        """
        # Create a fake pyATS Device with connection details
        device = Device(
            name='test-device',
            connections=AttrDict({
                'telnet': AttrDict({
                    'ip': ip_address('192.0.2.2'),
                    'port': 23
                })
            }),
            credentials=AttrDict({
                'default': AttrDict({
                    'username': 'admin',
                    'password': AttrDict({'plaintext': 'pass123'})
                })
            })
        )

        connector = TelnetConnector2(device)

        # Mock the Telnet connection object
        mock_conn_instance = MagicMock()
        mock_telnet.return_value = mock_conn_instance

        # Connect using mock connection
        connector.connect(connection=device.connections.telnet)
        mock_telnet.assert_called_once_with(host='192.0.2.2', port=23, timeout=10)

        # Simulate command execution
        mock_conn_instance.expect.return_value = (0, None, b"output text")
        output = connector.execute('show version', prompt=[r'#'])
        mock_conn_instance.write.assert_called_once_with(b'show version\n')
        self.assertEqual(output, "output text")

        # Test is_connected logic
        mock_conn_instance.eof = False
        self.assertTrue(connector.is_connected())

        # Disconnect and ensure the connection is closed
        connector.disconnect()
        mock_conn_instance.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
