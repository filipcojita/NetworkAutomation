"""This module connects to Cisco FTD through FDM's REST API and applies a full configuration.
The configuration includes creating security zones, assigning IPv4 addresses to interfaces,
creating network objects, access rules, static routes, and deploying the final setup."""

import ssl
import time

from pyats import aetest
from pyats.aetest.steps import Steps
from pyats.topology import loader
from swagger_connector import SwaggerConnector

# Disable SSL verification to allow connections to FDM with self-signed certificates
ssl._create_default_https_context = ssl._create_unverified_context

# Load testbed and retrieve the device named 'FTD'
tb = loader.load('mytopo.yaml')
device = tb.devices['FTD']


def create_security_zone(steps: Steps, swagger: SwaggerConnector):
    """
    Creates a security zone named 'AutoCreated1' and assigns it to a physical interface,
    unless the interface is already assigned to an existing zone.
    """
    with steps.start('Creating Security Zone'):
        already_configured = False

        # Retrieve all existing security zones from FDM
        security_zones = swagger.client.SecurityZone.getSecurityZoneList().result().items

        # Check if GigabitEthernet0/1 is already in a zone
        for zone in security_zones:
            for interface in zone.interfaces:
                if interface.hardwareName == 'GigabitEthernet0/1':
                    already_configured = True
                    break
            if already_configured:
                break

        # If not already assigned, create and assign the security zone
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
            print("Interface GigabitEthernet0/1 is already included in a SecurityZone. Skipping.")


def configure_interfaces(steps: Steps, swagger: SwaggerConnector):
    """
    Configures static IPv4 addresses on FTD interfaces based on the pyATS testbed file.
    """
    with steps.start("Configuring Interface"):
        interfaces_to_configure = [
            'GigabitEthernet0/0',
            'GigabitEthernet0/1',
            'GigabitEthernet0/2',
            'GigabitEthernet0/3'
        ]

        # Retrieve list of existing physical interfaces
        existing_interfaces = swagger.client.Interface.getPhysicalInterfaceList().result()['items']

        for obj in existing_interfaces:
            if obj.hardwareName in interfaces_to_configure:
                iface_name = obj.hardwareName
                dev_iface = device.interfaces.get(iface_name)

                if not dev_iface:
                    print(f"[WARNING] Interface {iface_name} not defined in testbed.")
                    continue

                # Initialize IPv4 structure if missing
                if obj.ipv4 is None:
                    obj.ipv4 = swagger.client.get_model('InterfaceIPv4')()
                if obj.ipv4.ipAddress is None:
                    obj.ipv4.ipAddress = swagger.client.get_model('HAIPv4Address')()

                # Assign IP address, netmask, and static configuration
                obj.ipv4.ipAddress.ipAddress = dev_iface.ipv4.ip.compressed
                obj.ipv4.ipAddress.netmask = dev_iface.ipv4.netmask.compressed
                obj.ipv4.dhcp = False
                obj.ipv4.ipType = 'STATIC'
                obj.enabled = True

                # Set interface name using alias or fallback to hardwareName
                obj.name = dev_iface.alias if dev_iface.alias else iface_name

                print(f"[INFO] Configuring {iface_name} with IP {obj.ipv4.ipAddress.ipAddress}")
                swagger.client.Interface.editPhysicalInterface(objId=obj.id, body=obj).result()


def create_access_rules(steps: Steps, swagger: SwaggerConnector):
    """
    Adds an access rule named 'Allow_Some' that permits all traffic to the 'AutoCreated1' security zone.
    """
    with steps.start('Creating Access Rule'):
        rule_name = "Allow_Some"
        ref = swagger.client.get_model('ReferenceModel')
        security_zone_model = swagger.client.get_model('SecurityZone')

        # Retrieve ID of the first access policy
        policy_list_id = swagger.client.AccessPolicy.getAccessPolicyList().result().items[0].id

        # Check for duplicate rules
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
                            security_zone_model(name="AutoCreated1")
                        )
                    ]
                )
            )
            print(res.result())
        else:
            print(f"Access Rule: {rule_name} already exists. Skipping.")


def create_network_objects(steps: Steps, swagger: SwaggerConnector):
    """
    Defines network and host objects for other nodes in the topology such as IOU2, CSR, Ubuntu, etc.
    """
    with steps.start('Creating Network Objects needed for Static Route'):
        model = swagger.client.get_model('NetworkObject')
        network_objects = swagger.client.NetworkObject.getNetworkObjectList().result().items

        # Add host objects if not present
        if len([obj for obj in network_objects if obj.name == 'IOU']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(name="IOU", subType="HOST", value="192.168.103.1")
            ).result()
        if len([obj for obj in network_objects if obj.name == 'CSR']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(name="CSR", subType="HOST", value="192.168.106.1")
            ).result()
        if len([obj for obj in network_objects if obj.name == 'IOSv']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(name="IOSv", subType="HOST", value="192.168.107.1")
            ).result()
        if len([obj for obj in network_objects if obj.name == 'IOU2']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(name="IOU2", subType="HOST", value="192.168.121.1")
            ).result()

        # Add network objects
        if len([obj for obj in network_objects if obj.name == 'UbuntuServerNetwork']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(name="UbuntuServerNetwork", subType="NETWORK", value="192.168.11.0/24")
            ).result()
        if len([obj for obj in network_objects if obj.name == 'DNSNetwork']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(name="DNSNetwork", subType="NETWORK", value="192.168.108.0/24")
            ).result()
        if len([obj for obj in network_objects if obj.name == 'DockerGuest1Network']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(name="DockerGuest1Network", subType="NETWORK", value="192.168.105.0/24")
            ).result()
        if len([obj for obj in network_objects if obj.name == 'IOU2Network']) == 0:
            swagger.client.NetworkObject.addNetworkObject(
                body=model(name="IOU2Network", subType="NETWORK", value="192.168.121.0/24")
            ).result()


def create_static_routes(steps: Steps, swagger: SwaggerConnector):
    """
    Creates static routes from the FTD to other subnets via specific interfaces and next-hop gateways.
    """
    with steps.start('Configuring static route'):
        model = swagger.client.get_model('StaticRouteEntry')
        v_router = swagger.client.Routing.getVirtualRouterList().result()['items'][0]

        ref = swagger.client.get_model('ReferenceModel')
        network_objects = swagger.client.NetworkObject.getNetworkObjectList().result().items
        interface_objects = swagger.client.Interface.getPhysicalInterfaceList().result()['items']

        # Match network objects by name
        csr_host_obj = next(filter(lambda o: o.name == 'CSR', network_objects))
        iosv_host_obj = next(filter(lambda o: o.name == 'IOSv', network_objects))
        iou2_host_obj = next(filter(lambda o: o.name == 'IOU', network_objects))
        ubuntu_server_network = next(filter(lambda o: o.name == 'UbuntuServerNetwork', network_objects))

        # Match interfaces by alias
        outside_interface = next(filter(lambda o: o.name == 'outside', interface_objects))
        iosv_interface = next(filter(lambda o: o.name == 'iosv', interface_objects))
        iou2_interface = next(filter(lambda o: o.name == 'iou2', interface_objects))

        def add_route(interface, gateway):
            # Add static route using interface and next-hop reference
            swagger.client.Routing.addStaticRouteEntry(
                parentId=v_router.id,
                body=model(
                    gateway=ref(id=gateway.id, name=gateway.name, type=gateway.type),
                    iface=ref(
                        id=interface.id,
                        name=interface.name,
                        hardwareName=interface.hardwareName,
                        type=interface.type
                    ),
                    ipType="IPv4",
                    type='staticrouteentry',
                    networks=[ref(
                        id=ubuntu_server_network.id,
                        name=ubuntu_server_network.name,
                        type=ubuntu_server_network.type
                    )]
                )
            )

        # Apply the static routes
        add_route(outside_interface, csr_host_obj)
        add_route(iosv_interface, iosv_host_obj)
        add_route(iou2_interface, iou2_host_obj)


def configure_fdm(steps: Steps):
    """
    Entry point for full REST configuration of the FTD via FDM Swagger API.
    Runs all setup steps in sequence and deploys the configuration.
    """
    with steps.start('Connecting to FDM'):
        swagger: SwaggerConnector = device.connections.rest['class'](device)
        swagger.connect(connection=device.connections.rest)

    with steps.start('Changing DHCP server'):
        dhcp_servers = swagger.client.DHCPServerContainer.getDHCPServerContainerList().result()
        for dhcp_server in dhcp_servers['items']:
            dhcp_server.servers = []  # Clear existing DHCP entries
            result = swagger.client.DHCPServerContainer.editDHCPServerContainer(
                objId=dhcp_server.id,
                body=dhcp_server
            ).result()
            print(result)

    # Call each config step
    create_security_zone(steps, swagger)
    configure_interfaces(steps, swagger)
    create_network_objects(steps, swagger)
    create_static_routes(steps, swagger)

    # Deploy the configuration
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
    pyATS test case class that triggers the full configuration workflow on FTD.
    """

    @aetest.test
    def configure_fdm_test(self, steps: Steps):
        """
        Invokes the configuration workflow on the FTD.
        """
        configure_fdm(steps)


# Launches pyATS execution if run as main script
if __name__ == '__main__':
    aetest.main()
