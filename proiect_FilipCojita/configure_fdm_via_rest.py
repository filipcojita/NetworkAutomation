"""Module for configuring FTD device using API Swagger with pyATS."""

import ssl
from pyats import aetest
from pyats.aetest.steps import Steps
from pyats.topology import loader
from swagger_connector import SwaggerConnector

ssl._create_default_https_context = ssl._create_unverified_context

tb = loader.load('mytopo.yaml')
device_fdm = tb.devices['FTD']


class Example3(aetest.Testcase):
    """Testcase pyATS for interface config and FTD policies."""

    @aetest.test
    def configure_fdm_interface(self, steps: Steps) -> None:
        """conf interfaces and network settings on FTD."""

        with steps.start('Connect to FDM'):
            swagger: SwaggerConnector = device_fdm.connections.rest['class'](device_fdm)
            swagger.connect(connection=device_fdm.connections.rest)

        with steps.start('Change DHCP server'):
            dhcp_servers = swagger.client.DHCPServerContainer.getDHCPServerContainerList().result()
            for dhcp_server in dhcp_servers['items']:
                dhcp_server.servers = []
                result = swagger.client.DHCPServerContainer.editDHCPServerContainer(
                    objId=dhcp_server.id,
                    body=dhcp_server
                ).result()
                print(result)

        with steps.start("configure Interface"):
            existing_object = swagger.client.Interface.getPhysicalInterfaceList().result()['items']
            for obj in existing_object:
                if obj.hardwareName == 'GigabitEthernet0/0':
                    obj.ipv4.ipAddress.ipAddress = device_fdm.interfaces['GigabitEthernet0/0'].ipv4.ip.compressed
                    obj.ipv4.ipAddress.netmask = device_fdm.interfaces['GigabitEthernet0/0'].ipv4.netmask.compressed
                    obj.enabled = True
                    obj.ipv4.dhcp = False
                    obj.ipv4.ipType = 'STATIC'
                    obj.name = device_fdm.interfaces['GigabitEthernet0/0'].alias
                elif obj.hardwareName == 'GigabitEthernet0/1':
                    obj.ipv4.ipAddress.ipAddress = device_fdm.interfaces['GigabitEthernet0/1'].ipv4.ip.compressed
                    obj.ipv4.ipAddress.netmask = device_fdm.interfaces['GigabitEthernet0/1'].ipv4.netmask.compressed
                    obj.enabled = True
                    obj.ipv4.dhcp = False
                    obj.ipv4.ipType = 'STATIC'
                    obj.name = device_fdm.interfaces['GigabitEthernet0/1'].alias
                elif obj.hardwareName == 'GigabitEthernet0/2':
                    obj.ipv4.ipAddress.ipAddress = device_fdm.interfaces['GigabitEthernet0/2'].ipv4.ip.compressed
                    obj.ipv4.ipAddress.netmask = device_fdm.interfaces['GigabitEthernet0/2'].ipv4.netmask.compressed
                    obj.enabled = True
                    obj.ipv4.dhcp = False
                    obj.ipv4.ipType = 'STATIC'
                    obj.name = device_fdm.interfaces['GigabitEthernet0/2'].alias
                else:
                    continue
                result = swagger.client.Interface.editPhysicalInterface(objId=obj.id, body=obj).result()
                print(result)

        with steps.start('create security zone'):
            ref = swagger.client.get_model('ReferenceModel')
            phy = swagger.client.Interface.getPhysicalInterfaceList().result()['items'][2]
            security_zone = swagger.client.get_model('SecurityZone')
            sz = security_zone(
                name='AutoCreated1',
                mode='ROUTED',
                interfaces=[ref(id=phy.id, name=phy.name, hardwareName=phy.hardwareName, type=phy.type)]
            )
            result = swagger.client.SecurityZone.addSecurityZone(body=sz).result()
            print(result)

        with steps.start('Creating Access Rule'):
            out = swagger.client.AccessPolicy.getAccessPolicyList()
            model = swagger.client.get_model('AccessRule')
            res = swagger.client.AccessPolicy.addAccessRule(
                parentId=out.result().items[0].id,
                body=model(
                    name='AccessRule',
                    ruleAction='PERMIT',
                )
            )
            print(res.result())

        with steps.start('Create network object'):
            network_object_model = swagger.client.get_model('NetworkObject')

            # create a 'host' type obj for ftd
            gateway_object = network_object_model(
                name="GATEWAY-OBJ",
                value="192.168.103.1",
                subType="HOST"
            )
            result1 = swagger.client.NetworkObject.addNetworkObject(body=gateway_object).result()
            print(f"[INFO] HOST object created: {result1.name} - {result1.value}")

            # create a 'network' type obj for ftd
            lan_object = network_object_model(
                name="LAN-OBJ",
                value="192.168.103.0/24",
                subType="NETWORK"
            )
            result2 = swagger.client.NetworkObject.addNetworkObject(body=lan_object).result()
            print(f"[INFO] NETWORK object created: {result2.name} - {result2.value}")

        with steps.start('Create Static Route'):
            model = swagger.client.get_model('StaticRouteEntry')
            ref = swagger.client.get_model('ReferenceModel')
            no = swagger.client.NetworkObject.getNetworkObjectList().result()['items']
            phy = swagger.client.Interface.getPhysicalInterfaceList().result()['items'][2]
            no1 = next(obj for obj in no if obj.name == "GATEWAY-OBJ")
            no2 = next(obj for obj in no if obj.name == "LAN-OBJ")
            st_model = model(
                gateway=ref(id=no1.id, name=no1.name, type=no1.type),
                iface=ref(
                    id=phy.id,
                    name=phy.name,
                    hardwareName=phy.hardwareName,
                    type=phy.type
                ),
                ipType='IPv4',
                type='staticrouteentry',
                networks=[ref(id=no2.id, name=no2.name, type=no2.type)]
            )

            vrf = swagger.client.Routing.getVirtualRouterList().result()['items'][0]
            print(vrf)
            swagger.client.Routing.addStaticRouteEntry(
                parentId=vrf.id,
                body=st_model
            )

        with steps.start('Deploy configuration'):
            response = swagger.client.Deployment.addDeployment().result()
            for _ in range(10):
                tasks = swagger.client.Deployment.getDeployment(objId=response.id).result()
                status = tasks['deploymentStatusMessages'][-1]
                if status.taskState == "FINISHED":
                    break
            else:
                print("Deployment failed")


if __name__ == '__main__':
    aetest.main()
