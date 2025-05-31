import random

class Port:
    def __init__(self, name, vlan, duplex, speed, state):
        self.name = name
        self.vlan = vlan
        self.duplex = duplex
        self.speed = speed
        self.state = state

    def __repr__(self):
        return f"Port({self.name}, VLAN: {self.vlan}, Duplex: {self.duplex}, Speed: {self.speed}, State: {self.state})"


class Switch:
    def __init__(self, model, serial):
        self.model = model
        self.serial = serial
        self.ports = {}  # Dictionary to store Port objects

    def add_switch_port(self, name, vlan, duplex, speed, state):
        if name in self.ports:
            print(f"Port {name} already exists.")
            return
        self.ports[name] = Port(name, vlan, duplex, speed, state)
        # print(f"Port {name} added successfully.")

    def remove_switch_port(self, name):
        if name in self.ports:
            del self.ports[name]
            print(f"Port {name} removed successfully.")
        else:
            print(f"Port {name} not found.")

    def update_switch_port(self, name, **kwargs):
        if name not in self.ports:
            print(f"Port {name} not found.")
            return
        for key, value in kwargs.items():
            if hasattr(self.ports[name], key):
                setattr(self.ports[name], key, value)
        print(f"Port {name} updated successfully.")

    def __iter__(self):
        return iter(self.ports.values())

    def __str__(self):
        return f"{self.serial}:{len(self.ports)}"

    def __repr__(self):
        return f"{self.model}:{self.serial}"


def generator_switches(count):
    models = ["Cisco 2960", "HP ProCurve", "Juniper EX2200", "Dell N2048"]
    duplex_modes = ["full", "half"]
    speeds = ["100Mbps", "1Gbps", "10Gbps"]
    states = ["up", "down", "err-disabled"]

    for _ in range(count):
        model = random.choice(models)
        serial = f"SN{random.randint(100000, 999999)}"
        switch = Switch(model, serial)

        num_ports = random.choice(range(8, 65, 4))
        for i in range(1, num_ports + 1):
            name = f"Gig{i}/0/1"
            vlan = random.randint(1, 4094)
            duplex = random.choice(duplex_modes)
            speed = random.choice(speeds)
            state = random.choice(states)
            switch.add_switch_port(name, vlan, duplex, speed, state)

        yield switch

count = 0

# Execution
for switch in generator_switches(100):
    if len(switch.ports) > 28 and any(port.vlan == 200 and port.speed in ["1Gbps", "10Gbps"] for port in switch):
        print(switch)
        count += 1

print(f"Total switches with 28 ports and vlan 200: {count}")

### sample output:
# SN852076:52
# Total switches with 28 ports and vlan 200: 1
