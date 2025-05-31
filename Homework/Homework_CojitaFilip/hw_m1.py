# Initialize an empty dictionary to store switch configuration
switch_config = {}

while True:
    swname = input("Enter switch name (or 'q' to quit): ")
    if swname == 'q':
        break  # Exit the loop if user enters 'q'

    if swname not in switch_config:
        switch_config[swname] = {}  # Create a new switch entry

    while True:
        swport = input(f"Enter port for {swname} (or 'q' to quit): ")
        if swport == 'q':
            break

        if swport not in switch_config[swname]:
            switch_config[swname][swport] = {"vlans": []}

        while True:
            vlan_input = input(f"Enter VLANs for {swname} {swport} (comma-separated, or 'q' to quit): ")
            if vlan_input == 'q':
                break

            # Split input into a list and remove spaces
            vlan_list = vlan_input.split(",")

            # Convert to integers and add to VLAN list (avoid duplicates)
            for vlan in vlan_list:
                vlan = vlan.strip()
                if vlan.isdigit() and int(vlan) not in switch_config[swname][swport]["vlans"]:
                    switch_config[swname][swport]["vlans"].append(int(vlan))

            print(f"Current VLANs for {swname} {swport}: {switch_config[swname][swport]['vlans']}")

print("\nFinal Switch Configuration:")
print(switch_config)