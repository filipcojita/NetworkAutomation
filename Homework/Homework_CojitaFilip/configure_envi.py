import subprocess
import telnetlib
import time
import telnetlib3
import asyncio

address = '192.168.0.100'
port = 5048

def set_ip_on_ubuntu():
    interface='ens4'
    ubuntu_ip='192.168.11.21/24'
    gateway_ip='192.168.11.1'

    subprocess.Popen(['sudo','ip','address',"add",ubuntu_ip,"dev",interface],stdout=subprocess.PIPE)
    subprocess.Popen(["sudo","ip","link","set",interface,"up"],stdout=subprocess.PIPE)

    dict_of_destinations = {"cloud": '192.168.12.0/24', "CSR": '192.168.101.0/24', "iosv": '192.168.102.0/24', "ftd":"192.168.103.0/24"}
    for value in dict_of_destinations.values():
        subprocess.Popen(['sudo',"ip","route","add",value,"via",gateway_ip],stdout=subprocess.PIPE)


# def set_ip_on_guest():
#     interface = 'eth0'
#     guest_ip = '192.168.101.100/24' #nu ia cu dhcp ip :(
#     destination_ip = '192.168.101.1/24'
#
#     new_te = telnetlib.Telnet("92.83.42.103", 5043) #telnet port de pe guest
#     new_te.write(f"ip addr add {guest_ip} dev {interface}".encode()) #nu merge
#     new_te.write(f"ip link set dev {interface} up".encode())
#     new_te.write(f"ip route add default via {destination_ip}".encode())

def ip_setting_function(te,i):
    te.write(f'int eth0/{str(i)}\n'.encode())
    te.expect([br"IOU1\(config-if\)#"])
    te.write(f'ip add 192.168.10{str(i)}.1 255.255.255.0\n'.encode())
    te.expect([br"IOU1\(config-if\)#"])
    te.write(f'no shutdown\n')
    te.expect([br"IOU1\(config-if\)#"])
    te.write(f'exit\n')
    te.expect([br"IOU1\(config\)#"])

def dhcp_exclude_interval(te,start,finish):
    te.write(f'ip dhcp excluded-address 192.168.101.{start} 192.168.101.{finish}\n'.encode())
    te.expect([b"IOU1\(config\)#"])

def dhcp_function(te):
    te.write(b'ip dhcp pool UbuntuDocker\n')
    te.expect([b"IOU1\(dhcp-config\)#"])
    te.write(b'network 192.168.101.0 255.255.255.0\n')
    te.expect([b"IOU1\(dhcp-config\)#"])
    te.write(b'default-router 192.168.101.1\n')
    te.expect([b"IOU1\(dhcp-config\)#"])
    te.write(b'dns-server 192.168.102.1\n')
    te.expect([b"IOU1\(dhcp-config\)#"])

def ssh_function(te):
    te.write(b'ip domain name local\n')
    te.expect([b"IOU1\(config\)#"])
    te.write(b'username admin password cisco\n')
    te.expect([b"IOU1\(config\)#"])
    te.write(b'crypto key generate rsa\n')
    time.sleep(3)
    te.write(b' \n')
    time.sleep(3)
    te.expect([b"IOU1\(config\)#"])
    te.write(b'ip ssh version 2\n')
    te.expect([b"IOU1\(config\)#"])
    te.write(b'line vty 0 4\n')
    te.expect([b"IOU1\(config-line\)#"])
    te.write(b'login local\n')
    te.expect([b"IOU1\(config-line\)#"])
    te.write(b'transport input ssh\n')
    te.expect([b"IOU1\(config-line\)#"])
    te.write(b'exit\n')
    te.expect([b"IOU1\(config\)#"])
    te.write(b'exit\n')

def router():
    host = '92.83.42.103'
    port = 5042 #router port
    interface_number = 4

    te = telnetlib.Telnet(host,port)

    te.write(b'')

    #setting up ip int g0/0 from ubuntu
    te.write(b'conf t\n')
    te.expect([b"IOU1\(config\)#"])
    te.write(b'int eth0/0\n')
    te.expect([b"IOU1\(config-if\)#"])
    te.write(b'ip add 192.168.11.1 255.255.255.0\n')
    te.expect([b"IOU1\(config-if\)#"])
    te.write(b'no shutdown\n')

    #setting up ip other interfaces
    for i in range(1,interface_number):
       ip_setting_function(te,i)

    #setting up extra ip interface g1/0
    te.write(b'int eth1/0\n')
    te.expect([b"IOU1\(config-if\)#"])
    te.write(b'ip add 192.168.104.1 255.255.255.0\n')
    te.expect([b"IOU1\(config-if\)#"])
    te.write(b'no shutdown\n')
    te.expect([b"IOU1\(config-if\)#"])
    te.write(b'exit\n')
    te.expect([b"IOU1\(config\)#"])
    te.write(b'ip route 0.0.0.0 0.0.0.0 192.168.11.21\n')
    te.expect([b"IOU1\(config\)#"])

    #dhcp
    dhcp_exclude_interval(te,1,99)
    dhcp_exclude_interval(te,200,254)
    dhcp_function(te)

    #ssh
    te.write(b'exit\n')
    te.expect([b"IOU1\(config\)#"])
    ssh_function(te)
    te.write(b'exit\n')

# List of all devices
ip_addresses = [
    "192.168.11.1",
    "192.168.101.1", "192.168.101.2",
    "192.168.102.1", "192.168.102.2",
    "192.168.103.1", "192.168.103.2",
]

def ping_ip(ip):
    try:
        output = subprocess.check_output(
            ["ping", "-c", "2", ip],
            stderr=subprocess.STDOUT,
            text=True
        )
        if "0 received" in output or "100% packet loss" in output:
            return False
        return True
    except subprocess.CalledProcessError:
        return False

def connectivity():
    unreachable = []

    print("=== PING TEST START ===")
    for ip in ip_addresses:
        print(f"Pinging {ip}...", end=" ")
        if ping_ip(ip):
            print("✅ Reachable")
        else:
            print("❌ Unreachable")
            unreachable.append(ip)

    print("\n=== SUMMARY ===")
    if not unreachable:
        print("✅ All devices are reachable.")
    else:
        print("❌ The following devices are unreachable:")
        for ip in unreachable:
            print(f" - {ip}")

async def configure_csr_device(address, port, user, password, hostname):
    t_reader, t_writer = await telnetlib3.open_connection(address, port)
    t_writer.write("\n")

    try:
        response = await asyncio.wait_for(t_reader.read(200), timeout=5)  # generic read
        print("Prompt received:", response)  # Debugging line

        if 'initial configuration dialog? [yes/no]' in response:
            t_writer.write('yes\n')
            await t_reader.readuntil("management setup? [yes/no]:")
            t_writer.write('yes\n')
            await t_reader.readuntil("host name [Router]:")
            t_writer.write(f'{hostname}\n')
            await t_reader.readuntil("Enter enable secret:")
            t_writer.write(f'{password}\n')
            await t_reader.readuntil("Enter enable password:")
            t_writer.write(f'{password}\n')
            await t_reader.readuntil("Enter virtual terminal password:")
            t_writer.write(f'{password}\n')
            await t_reader.readuntil("SNMP Network Management? [yes]:")
            t_writer.write('no\n')
            await t_reader.readuntil("interface summary:")
            t_writer.write('GigabitEthernet1\n')
            await t_reader.readuntil("IP on this interface? [yes]:")
            t_writer.write('yes\n')
            await t_reader.readuntil("IP address for this interface:")
            t_writer.write('192.168.102.2\n')
            await t_reader.readuntil("mask for this interface [255.255.255.0] :")
            t_writer.write('255.255.255.0\n')
            await t_reader.readuntil("Enter your selection [2]:")
            t_writer.write('2\n')

            await asyncio.sleep(25)
            t_writer.write('\n')
            await asyncio.sleep(5)
            t_writer.write('\n')
            await t_reader.readuntil("Router>")
            t_writer.write('en\n')
            await t_reader.readuntil("Password:")
            t_writer.write(f'{password}\n')
            await t_reader.readuntil("Router#")
            t_writer.write('conf t\n')
            await t_reader.readuntil("Router(config)#")
            t_writer.write('ip route 192.168.11.0 255.255.255.0 192.168.102.1\n')
            await t_reader.readuntil("Router(config)#")
            t_writer.write('ip route 192.168.101.0 255.255.255.0 192.168.102.1\n')
            await t_reader.readuntil("Router(config)#")

        elif 'Router>' in response:
            # Directly in user mode — configure manually
            t_writer.write('enable\n')
            await t_reader.readuntil(b"Password:")
            t_writer.write(f'{password}\n')
            await t_reader.readuntil(b"Router#")
            t_writer.write('conf t\n')
            await t_reader.readuntil(b"Router(config)#")
            t_writer.write('int GigabitEthernet1\n')
            await t_reader.readuntil(b"Router(config-if)#")
            t_writer.write('no ip address\n')
            await t_reader.readuntil(b"Router(config-if)#")
            t_writer.write('ip address 192.168.101.2 255.255.255.0\n')
            await t_reader.readuntil(b"Router(config-if)#")
            t_writer.write('no shutdown\n')
            await t_reader.readuntil(b"Router(config-if)#")
            t_writer.write('exit\n')
            await t_reader.readuntil(b"Router(config)#")
            t_writer.write('exit\n')
            print("Router is configured in user mode.")

    except asyncio.TimeoutError:
        print("TimeoutError: No recognizable prompt received.")

#setting up iosv router
def router_iosv():
    host = '92.83.42.103'
    port = 5019  # router port

    te = telnetlib.Telnet(host, port)

    te.write(b'')

    # setting up ip int g0/0 from ubuntu
    te.write(b'conf t\n')
    te.expect([b"iosv\(config\)#"])
    te.write(b'int GigabitEthernet0/0\n')
    te.expect([b"iosv\(config-if\)#"])
    te.write(b'no ip add\n')
    te.expect([b'iosv\(config-if\)#'])
    te.write(b'ip add 192.168.102.2 255.255.255.0\n')
    te.expect([b"iosv\(config-if\)#"])
    te.write(b'no shutdown\n')
    te.expect([b"iosv\(config-if\)#"])
    te.write(b'exit\n')
    te.expect([b'iosv\(config\)#'])
    te.write(b'exit\n')

while True:
    print("1.Set IP on Ubuntu Server and Configure")
    print("2.Configure Router")
    print("3.CHECK CONNECTIVITY")
    print("4.Configure CSR Router")
    print("5.Configure iosv Router")
    print("6.Exit")
    option=input("Choose an option:")

    match option:
        case "1":
            set_ip_on_ubuntu()
            print("Command executed successfully!")
        case "2":
            router()
            print("Command executed successfully!")
        case "3":
            connectivity()
            print("Command executed successfully!")
        case "4":
            asyncio.run(configure_csr_device(address, port, user='admin', password='Cisco!12', hostname="Router"))
            print("Command executed successfully!")
        case "5":
            router_iosv()
            print("Command executed successfully!")
        case "6":
            break

    time.sleep(2)