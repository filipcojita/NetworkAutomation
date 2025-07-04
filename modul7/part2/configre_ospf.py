"""Added docstrings for module"""
import ipaddress

from pyats import aetest
from pyats.aetest.steps import Steps, Step  # pylint: disable=unused-import
from pyats.topology import loader
from genie.libs.conf.ospf.ospf import Ospf
from genie.libs.conf.interface.iosxe import Interface
# from genie.libs.conf.device import Device

tb = loader.load('testbed_example2.yaml')
device_csr = tb.devices['em-r2']
device_iosv = tb.devices['iosv']

#
# class Example(aetest.Testcase):
#     """This is docstring for class"""
#
#     @aetest.test
#     def configure_ospf_csr(self, steps: Steps):
#         """This is docstring for method"""
#         with steps.start('Connect to device'):
#             device_csr.connect(log_stdout=True)
#
#         with steps.start('Create Interface Object CSR'):
#             intf = Interface(name='GigabitEthernet2')
#             intf.device = device_csr
#             intf.ipv4 = ipaddress.IPv4Interface('192.168.105.1/24')
#             config = intf.build_config(apply=False)
#             device_csr.configure(config.cli_config.data)
#
#         with steps.start('Configure OSPF on CSR'):
#             ospf = Ospf()
#             ospf.device_attr[device_csr].vrf_attr['default'].instance = '1'
#             ospf.device_attr[device_csr].vrf_attr['default'].router_id = '192.168.102.2'
#             area = ospf.device_attr[device_csr].vrf_attr['default'].area_attr[0]
#             area.area = 0
#             area.networks.append('192.168.105.0 0.0.0.255')
#             ospf.build_config(devices=[device_csr])


class Example2(aetest.Testcase):
    @aetest.test
    def configure_ospf_iosv(self, steps: Steps):
        with steps.start('Connect to IOSv'):
            device_iosv.connect(log_stdout=True)

        with steps.start('Create Interface Object IOSv'):
            intf_name = 'to_FTD'
            intf = device_iosv.interfaces[intf_name]
            int_f = Interface(name=intf.name)
            int_f.device = device_iosv
            int_f.ipv4 = intf.ipv4
            config = int_f.build_config(apply=False)
            device_iosv.configure(config.cli_config.data)

        with steps.start('Configure OSPF on IOSV'):
            ospf = Ospf()
            ospf.device_attr[device_iosv].vrf_attr['default'].instance = '1'
            ospf.device_attr[device_iosv].vrf_attr['default'].router_id = '192.168.102.2'
            area = ospf.device_attr[device_iosv].vrf_attr['default'].area_attr[0]
            area.area = 0
            # area.networks.append('192.168.107.0 0.0.0.255')
            config = ospf.build_config(devices=[device_iosv])
            print(config)

            with steps.start('configure DHCP on IOSv'):
                dhcp_template = """
ip dhcp excluded-address {device_interface}
ip dhcp pool {dhcp_pool_name}
 network {network} {mask}
 default-router {gateway}
 dns-server {dns_server}
 lease 0 12
        """
                intf_name = 'to_DNS'
                intf = device_iosv.interfaces[intf_name]
                iosv_conf = dhcp_template.format(
                    device_interface=intf.ipv4.ip.compressed,
                    dhcp_pool_name=device_iosv.custom.get('dhcp_pool_name'),
                    network=intf.ipv4.network.network_address.compressed,
                    mask=intf.ipv4.netmask.compressed,
                    gateway=intf.ipv4.ip.compressed,
                    dns_server=device_iosv.custom.get('dns_server')
                )

                device_iosv.configure(iosv_conf)



if __name__ == '__main__':
    aetest.main()
