"""
5 tests for the network automation project
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


class TestUbuntuSetup(unittest.TestCase):
    """Unit tests for UbuntuNetworkConfigurator."""

    @patch('ubuntu_setup.subprocess.run')
    def test_configure_runs_expected_commands(self, mock_run):
        """Test if configure() runs the expected network commands."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""

        configurator = UbuntuNetworkConfigurator(
            interface='ens4',
            ip='192.168.11.21/24',
            gateway='192.168.11.1'
        )
        configurator.configure()

        expected_calls = [
            call(['sudo', 'ip', 'address', 'add', '192.168.11.21/24', 'dev', 'ens4'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'link', 'set', 'ens4', 'up'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.12.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.101.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.102.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.103.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.105.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.106.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.107.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.108.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
            call(['sudo', 'ip', 'route', 'add', '192.168.109.0/24', 'via', '192.168.11.1'],
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True),
        ]

        self.assertEqual(mock_run.call_count, len(expected_calls))
        mock_run.assert_has_calls(expected_calls, any_order=False)

    @patch('ubuntu_setup.subprocess.run')
    def test_run_command_handles_failure(self, mock_run):
        """Test run_command() prints error message on failure."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Command failed"

        configurator = UbuntuNetworkConfigurator()
        with patch('builtins.print') as mock_print:
            configurator.run_command(['fake', 'cmd'])

        mock_print.assert_any_call("Error: Command failed")

    @patch('ubuntu_setup.subprocess.run')
    def test_configure_with_custom_interface_and_ip(self, mock_run):
        """Test configure() with custom interface and IP address."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        configurator = UbuntuNetworkConfigurator(
            interface='eth0', ip='10.0.0.5/24', gateway='10.0.0.1'
        )
        configurator.configure()

        mock_run.assert_any_call(
            ['sudo', 'ip', 'address', 'add', '10.0.0.5/24', 'dev', 'eth0'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        mock_run.assert_any_call(
            ['sudo', 'ip', 'link', 'set', 'eth0', 'up'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )


class TestSSHConnectorParamiko(unittest.TestCase):
    """Unit tests for SSHConnectorParamiko class."""

    @patch('ssh_connector_paramiko.paramiko.SSHClient')
    def test_ssh_connect_and_execute(self, mock_ssh_client):
        """Test SSH connection and command execution via Paramiko."""
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
    """Unit tests for TelnetConnector2 class."""

    @patch('telnet_connector2.telnetlib.Telnet')
    def test_telnet_connect_and_execute(self, mock_telnet):
        """Test Telnet connection and command execution."""
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

if __name__ == '__main__':
    unittest.main()
