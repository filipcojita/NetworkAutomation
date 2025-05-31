"""
usage file - configure 1 specific device from topology
"""
from pyats import aetest
from pyats.topology import loader

from telnet_connector2 import TelnetConnector2
from ssh_connector_paramiko import SSHConnectorParamiko


# Load the topology
tb = loader.load('mytopo.yaml')

# Specify the device name here
DEVICE_NAME = 'IOU1'  # Change this as needed


class OneDeviceTelnetSSHTest(aetest.Testcase):

    @aetest.test
    def telnet_configure(self):
        dev = tb.devices[DEVICE_NAME]

        if 'telnet' not in dev.connections:
            self.passed(f"{DEVICE_NAME} does not have a telnet connection defined.")
            return

        print(f"[Telnet] Connecting to {DEVICE_NAME}")
        conn = dev.connections.telnet
        telnet_connector = TelnetConnector2(dev)

        try:
            telnet_connector.connect(connection=conn)
            telnet_connector.do_initial_configuration()
            print(f"[Telnet] Configuration complete for {DEVICE_NAME}")
        finally:
            telnet_connector.disconnect()
            print(f"[Telnet] Disconnected from {DEVICE_NAME}")

    @aetest.test
    def ssh_configure(self):
        dev = tb.devices[DEVICE_NAME]

        if 'ssh' not in dev.connections:
            self.passed(f"{DEVICE_NAME} does not have an ssh connection defined.")
            return

        print(f"[SSH] Connecting to {DEVICE_NAME}")
        ssh = SSHConnectorParamiko(dev)

        try:
            ssh.connect()
            ssh.configure_interfaces()
            ssh.configure_static_routes()
            print(f"[SSH] Configuration complete for {DEVICE_NAME}")
        except Exception as e:
            print(f"[SSH] Error configuring {DEVICE_NAME}: {e}")
        finally:
            try:
                ssh.disconnect()
            except Exception:
                pass  # Ignore disconnect errors
            print(f"[SSH] Disconnected from {DEVICE_NAME}")


if __name__ == '__main__':
    aetest.main()
