"""Added docstrings for module"""
import ssl
import time

from pyats import aetest
from pyats.aetest.steps import Steps
from pyats.topology import loader
from  swagger_connector import SwaggerConnector
ssl._create_default_https_context = ssl._create_unverified_context


tb = loader.load('mytopo.yaml')
device = tb.devices['FTD']

def create_security_zone(steps: Steps, swagger: SwaggerConnector):
    """
    Creates a security zone
    """
    with steps.start('Creating Security Zone'):
        already_configured = False
        security_zones = swagger.client.SecurityZone.getSecurityZoneList().result().items
        for zone in security_zones:
            for interface in zone.interfaces:
                if interface.hardwareName == 'GigabitEthernet0/1':
                    already_configured = True
                    break
            if already_configured:
                break

        if not already_configured:
            ref = swagger.client.get_model('ReferenceModel')
            phy = swagger.client.Interface.getPhysicalInterfaceList().result()['items'][2]
            security_zone = swagger.client.get_model('SecurityZone')
            sz = security_zone(
                name='AutoCreated1',
                mode='ROUTED',
                interfaces=[
                    ref(
                        id=phy.id,
                        name=phy.name,
                        hardwareName=phy.hardwareName,
                        type=phy.type
                    )
                ]
            )
            result = swagger.client.SecurityZone.addSecurityZone(body=sz).result()
            print(result)
        else:
            print("Interface GigabitEthernet0/1 is already included in a SecurityZone."
                  " Skipping creating a new one.")

def configure_interfaces(steps: Steps, swagger: SwaggerConnector):
    """
    Configures ipv4 addresses on interfaces
    """
    with steps.start("Configuring Interface"):
        existing_object = swagger.client.Interface.getPhysicalInterfaceList().result()['items']
        for obj in existing_object:
            print(f"[DEBUG] Editing interface: {obj.hardwareName}")
            print(f"[DEBUG] Existing ipv4: {obj.ipv4}")
            if obj.hardwareName == 'GigabitEthernet0/0':
                print(f"[DEBUG] Editing interface: {obj.hardwareName}")
                print(f"[DEBUG] Existing ipv4: {obj.ipv4}")

                # Defensive init
                if obj.ipv4 is None:
                    obj.ipv4 = swagger.client.get_model('InterfaceIPv4')()
                if obj.ipv4.ipAddress is None:
                    obj.ipv4.ipAddress = swagger.client.get_model('HAIPv4Address')()

                interface_ip = device.interfaces['GigabitEthernet0/0'].ipv4.ip.compressed
                interface_mask = device.interfaces['GigabitEthernet0/0'].ipv4.netmask.compressed

                obj.ipv4.ipAddress.ipAddress = interface_ip
                obj.ipv4.ipAddress.netmask = interface_mask
                obj.enabled = True
                obj.ipv4.dhcp = False
                obj.ipv4.ipType = 'STATIC'
                swagger.client.Interface.editPhysicalInterface(objId=obj.id, body=obj).result()
            elif obj.hardwareName == 'GigabitEthernet0/1':
                print(f"[DEBUG] Editing interface: {obj.hardwareName}")
                print(f"[DEBUG] Existing ipv4: {obj.ipv4}")

                # Defensive init
                if obj.ipv4 is None:
                    obj.ipv4 = swagger.client.get_model('InterfaceIPv4')()
                if obj.ipv4.ipAddress is None:
                    obj.ipv4.ipAddress = swagger.client.get_model('HAIPv4Address')()

                interface_ip = device.interfaces['GigabitEthernet0/1'].ipv4.ip.compressed
                interface_mask = device.interfaces['GigabitEthernet0/1'].ipv4.netmask.compressed

                obj.ipv4.ipAddress.ipAddress = interface_ip
                obj.ipv4.ipAddress.netmask = interface_mask
                obj.enabled = True
                obj.ipv4.dhcp = False
                obj.ipv4.ipType = 'STATIC'
                swagger.client.Interface.editPhysicalInterface(objId=obj.id, body=obj).result()
            elif obj.hardwareName == 'GigabitEthernet0/2':
                print(f"[DEBUG] Editing interface: {obj.hardwareName}")
                print(f"[DEBUG] Existing ipv4: {obj.ipv4}")

                # Defensive init
                if obj.ipv4 is None:
                    obj.ipv4 = swagger.client.get_model('InterfaceIPv4')()
                if obj.ipv4.ipAddress is None:
                    obj.ipv4.ipAddress = swagger.client.get_model('HAIPv4Address')()

                interface_ip = device.interfaces['GigabitEthernet0/2'].ipv4.ip.compressed
                interface_mask = device.interfaces['GigabitEthernet0/2'].ipv4.netmask.compressed

                obj.ipv4.ipAddress.ipAddress = interface_ip
                obj.ipv4.ipAddress.netmask = interface_mask
                obj.enabled = True
                obj.ipv4.dhcp = False
                obj.ipv4.ipType = 'STATIC'
                swagger.client.Interface.editPhysicalInterface(objId=obj.id, body=obj).result()
            elif obj.hardwareName == 'GigabitEthernet0/3':
                print(f"[DEBUG] Editing interface: {obj.hardwareName}")
                print(f"[DEBUG] Existing ipv4: {obj.ipv4}")

                # Defensive init
                if obj.ipv4 is None:
                    obj.ipv4 = swagger.client.get_model('InterfaceIPv4')()
                if obj.ipv4.ipAddress is None:
                    obj.ipv4.ipAddress = swagger.client.get_model('HAIPv4Address')()

                interface_ip = device.interfaces['GigabitEthernet0/3'].ipv4.ip.compressed
                interface_mask = device.interfaces['GigabitEthernet0/3'].ipv4.netmask.compressed

                obj.ipv4.ipAddress.ipAddress = interface_ip
                obj.ipv4.ipAddress.netmask = interface_mask
                obj.enabled = True
                obj.ipv4.dhcp = False
                obj.ipv4.ipType = 'STATIC'
                swagger.client.Interface.editPhysicalInterface(objId=obj.id, body=obj).result()

def create_access_rules(steps: Steps, swagger: SwaggerConnector):
    """
    Creates an access rule to allow all traffic to security zone 0
    """
    with steps.start('Creating Access Rule'):
        rule_name = "Allow_Some"
        ref = swagger.client.get_model('ReferenceModel')
        security_zone_model = swagger.client.get_model('SecurityZone')
        policy_list_id = swagger.client.AccessPolicy.getAccessPolicyList().result().items[0].id
        access_rules = swagger.client.AccessPolicy.getAccessRuleList(parentId=policy_list_id).result().items
        if len([rule for rule in access_rules if rule.name == rule_name]) == 0:
            model = swagger.client.get_model('AccessRule')
            res = swagger.client.AccessPolicy.addAccessRule(
                parentId=policy_list_id,
                body=model(
                    name=rule_name,
                    ruleAction='PERMIT',
                    destinationZones=[
                        ref(
                            security_zone_model(
                               name="AutoCreated1"
                            )
                        )
                    ]
                )
            )
            print(res.result())
        else:
            print(f"Access Rule: {rule_name} already exists. Skipping.")

def create_network_objects(steps: Steps, swagger: SwaggerConnector):
    """
    Creates the 'NETWORK' network objects for networks towards UbuntuServer, DNS & DockerGuest1
    Creates CSR, IOU, V15 HOST network objects
    """
    with steps.start('Creating Network Objects needed for Static Route'):
        model = swagger.client.get_model('NetworkObject')
        network_objects = swagger.client.NetworkObject.getNetworkObjectList().result().items
        # Hosts
        if len([obj for obj in network_objects if obj.name == 'IOU']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(
                    name="IOU",
                    # Cand creezi manual si dai add, iti apare type: Host
                    subType="HOST",
                    value="192.168.103.1"
                )
            ).result()
        if len([obj for obj in network_objects if obj.name == 'CSR']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(
                    name="CSR",
                    subType="HOST",
                    value="40.40.40.1"
                )
            ).result()
        # if len([obj for obj in network_objects if obj.name == 'V15']) == 0:
        #     swagger.client.NetworkObject.addNetworkObject(
        #         body=model(
        #             name="V15",
        #             subType="HOST",
        #             value="10.10.10.1"
        #         )
        #     ).result()
        # Networks
        if len([obj for obj in network_objects if obj.name == 'UbuntuServerNetwork']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(
                    name="UbuntuServerNetwork",
                    subType="NETWORK",
                    value="192.168.11.0/24"
                )
            ).result()
        if len([obj for obj in network_objects if obj.name == 'DNSNetwork']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(
                    name="DNSNetwork",
                    subType="NETWORK",
                    value="20.20.20.0/24"
                )
            ).result()
        if len([obj for obj in network_objects if obj.name == 'DockerGuest1Network']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(
                    name="DockerGuest1Network",
                    subType="NETWORK",
                    value="50.50.50.0/24"
                )
            ).result()

# Aici crapa cu types =/
def create_static_routes(steps: Steps, swagger: SwaggerConnector):
    """
    Creates static route objects towards UbuntuServer, DNS, DockerGuest1 networks
    """
    with steps.start('Configuring static route'):
        model = swagger.client.get_model('StaticRouteEntry')
        v_router = swagger.client.Routing.getVirtualRouterList().result()['items'][0]

        ref = swagger.client.get_model('ReferenceModel')
        network_objects = swagger.client.NetworkObject.getNetworkObjectList().result().items
        interface_objects = swagger.client.Interface.getPhysicalInterfaceList().result()['items']

        csr_host_obj = next(filter(lambda o: o.name == 'CSR', network_objects))
        ubuntu_server_network = next(filter(lambda o: o.name == 'UbuntuServerNetwork', network_objects))
        dns_server_network = next(filter(lambda o: o.name == 'DNSNetwork', network_objects))
        docker_guest1_network = next(filter(lambda o: o.name == 'DockerGuest1Network', network_objects))

        interface_g01 = next(filter(lambda o: o.hardwareName == 'GigabitEthernet0/2', interface_objects))

        # Completează valorile lipsă (temporar)
        for obj in [csr_host_obj, ubuntu_server_network, dns_server_network, docker_guest1_network]:
            if not obj.name:
                obj.name = "AutoGenerated"
            if not obj.type:
                obj.type = "networkobject"

        if not interface_g01.name:
            interface_g01.name = interface_g01.hardwareName
        if not interface_g01.type:
            interface_g01.type = "physicalinterface"

        print("[DEBUG] Static route components:")
        print(f"  CSR  -> id: {csr_host_obj.id}, name: {csr_host_obj.name}, type: {csr_host_obj.type}")
        print(
            f"  IF   -> id: {interface_g01.id}, name: {interface_g01.name}, type: {interface_g01.type}, hw: {interface_g01.hardwareName}")
        print(
            f"  DEST -> id: {ubuntu_server_network.id}, name: {ubuntu_server_network.name}, type: {ubuntu_server_network.type}")

        def add_route(destination_obj):
            swagger.client.Routing.addStaticRouteEntry(
                parentId=v_router.id,
                body=model(
                    gateway=ref(
                        id=csr_host_obj.id,
                        name=csr_host_obj.name,
                        type=csr_host_obj.type
                    ),
                    iface=ref(
                        id=interface_g01.id,
                        name=interface_g01.name,
                        hardwareName=interface_g01.hardwareName,
                        type=interface_g01.type
                    ),
                    ipType="IPv4",
                    type='staticrouteentry',
                    networks=[
                        ref(
                            id=destination_obj.id,
                            name=destination_obj.name,
                            type=destination_obj.type
                        )
                    ]
                )
            )

        # Adaugă cele 3 rute
        add_route(ubuntu_server_network)
        add_route(dns_server_network)
        add_route(docker_guest1_network)

def configure_fdm(steps: Steps):
    """
    Connects to FDM via REST & performs all configurations
    """
    with steps.start('Connecting to FDM'):
        swagger: SwaggerConnector = device.connections.rest['class'](device)
        swagger.connect(connection=device.connections.rest)

    with steps.start('Changing DHCP server'):
        dhcp_servers = swagger.client.DHCPServerContainer.getDHCPServerContainerList().result()
        for dhcp_server in dhcp_servers['items']:
            dhcp_server.servers = []
            result = swagger.client.DHCPServerContainer.editDHCPServerContainer(
                objId=dhcp_server.id,
                body=dhcp_server
            ).result()
            print(result)

    create_security_zone(steps, swagger)
    configure_interfaces(steps, swagger)
    create_network_objects(steps, swagger)
    create_static_routes(steps, swagger)

    with steps.start('Deploying configuration'):
        response = swagger.client.Deployment.addDeployment().result()
        for _ in range(10):
            time.sleep(3)
            tasks = swagger.client.Deployment.getDeployment(objId=response.id).result()
            if len(tasks['deploymentStatusMessages']) == 0:
                continue
            status = tasks['deploymentStatusMessages'][-1]
            if status['taskState'] == "FINISHED":
                break
        else:
            print("Deployment failed or is taking too much time.")

class REST_config(aetest.Testcase):
    """
    Configures FTD via FDM Swagger client
    """

    @aetest.test
    def configure_fdm_test(self, steps: Steps):
        """
        Configures FDM via REST
        """
        configure_fdm(steps)

if __name__ == '__main__':
    aetest.main()