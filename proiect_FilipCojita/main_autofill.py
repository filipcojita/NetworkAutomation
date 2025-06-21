import time
from pyats import aetest
from pyats.topology import loader
from autofill_engine import autofill_missing_data
from ubuntu_setup import UbuntuNetworkConfigurator
from telnet_connector2 import TelnetConnector2
from ssh_connector_paramiko import SSHConnectorParamiko

# Load the topology
tb = loader.load('mytopo.yaml')

class AutoFillDevicesTest(aetest.Testcase):

    @aetest.test
    def configure_devices(self):
        start_time = time.time()

        autofill_missing_data(tb)

        for device_name, dev in tb.devices.items():
            print(f"\n[START] Configuring device: {device_name}")

            # Handle Ubuntu separately
            if dev.os == 'linux' and dev.type == 'ubuntu':
                print(f"[Ubuntu] Running local configuration for {device_name}")
                try:
                    ubuntu = UbuntuNetworkConfigurator(dev, testbed_path="mytopo.yaml")
                    ubuntu.configure()
                except Exception as e:
                    print(f"[Ubuntu] Error configuring {device_name}: {e}")
                continue

            # Telnet configuration
            if 'telnet' in dev.connections:
                print(f"[Telnet] Connecting to {device_name}")
                conn = dev.connections.telnet
                telnet_connector = TelnetConnector2(dev)
                try:
                    telnet_connector.connect(connection=conn)
                    telnet_connector.do_initial_configuration()
                    print(f"[Telnet] Configuration complete for {device_name}")
                except Exception as e:
                    print(f"[Telnet] Error configuring {device_name}: {e}")
                finally:
                    try:
                        telnet_connector.disconnect()
                    except Exception:
                        pass
                    print(f"[Telnet] Disconnected from {device_name}")

            # SSH configuration (skip FTD)
            if 'ssh' in dev.connections and dev.os != 'ftd':
                print(f"[SSH] Connecting to {device_name}")
                ssh = SSHConnectorParamiko(dev)
                try:
                    ssh.connect()
                    ssh.configure_interfaces()
                    ssh.configure_routing()
                    ssh.configure_dhcp()
                    print(f"[SSH] Configuration complete for {device_name}")
                except Exception as e:
                    print(f"[SSH] Error configuring {device_name}: {e}")
                finally:
                    try:
                        ssh.disconnect()
                    except Exception:
                        pass
                    print(f"[SSH] Disconnected from {device_name}")

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"\n Total configuration time: {elapsed:.2f} seconds")

if __name__ == '__main__':
    aetest.main()
