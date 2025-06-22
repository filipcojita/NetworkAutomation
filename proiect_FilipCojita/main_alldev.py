"""
usage file - configure all devices in topology
"""
from pyats import aetest
from pyats.topology import loader
import logging
from ubuntu_setup import UbuntuNetworkConfigurator
from telnet_connector2 import TelnetConnector2
from ssh_connector_paramiko import SSHConnectorParamiko

# Load the topology
tb = loader.load('mytopo.yaml')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, encoding='utf-8')

class AllDevicesTelnetSSHTest(aetest.Testcase):

    @aetest.test
    def configure_all_devices(self):
        for device_name, dev in tb.devices.items():
            print(f"\nConfiguring device: {device_name}")

            # Handle Ubuntu separately
            if dev.os == 'linux' and dev.type == 'ubuntu':
                print(f"[Ubuntu] Running local configuration for {device_name}")
                try:
                    ubuntu = UbuntuNetworkConfigurator(dev, testbed_path="mytopo.yaml")
                    ubuntu.configure()
                except Exception as e:
                    print(f"[Ubuntu] Error configuring {device_name}: {e}")
                continue

            # 1) Telnet configuration (if connection exists)
            if 'telnet' in dev.connections:
                print(f"[Telnet] Connecting to {device_name}")
                conn = dev.connections.telnet
                telnet_connector = TelnetConnector2(dev)

                try:
                    telnet_connector.connect(connection=conn)
                    telnet_connector.do_initial_configuration()
                    print(f"[Telnet] Configuration complete for {device_name}")
                finally:
                    telnet_connector.disconnect()
                    print(f"[Telnet] Disconnected from {device_name}")
            else:
                print(f"[Telnet] No telnet connection defined for {device_name}")

            # 2) SSH configuration (only if ssh connection exists AND device is NOT FTD)
            if 'ssh' in dev.connections:
                # Check if device is FTD — skip SSH for FTD devices
                if 'ftd' in device_name.lower():
                    print(f"[SSH] Skipping SSH configuration for FTD device {device_name}")
                    continue

                print(f"[SSH] Connecting to {device_name}")
                ssh = SSHConnectorParamiko(dev)

                try:
                    ssh.connect()
                    ssh.configure_interfaces()
                    ssh.configure_static_routes()
                    print(f"[SSH] Configuration complete for {device_name}")
                except Exception as e:
                    print(f"[SSH] Error configuring {device_name}: {e}")
                finally:
                    try:
                        ssh.disconnect()
                    except Exception:
                        pass  # Ignore disconnect errors
                    print(f"[SSH] Disconnected from {device_name}")
            else:
                print(f"[SSH] No ssh connection defined for {device_name}")


if __name__ == '__main__':
    aetest.main()
