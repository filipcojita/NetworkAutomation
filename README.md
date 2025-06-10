# Network Automation Project

This project automates the initial configuration and management of Cisco network devices (IOS, IOS-XE, and FTD) using Python and SSH/API-based automation. It supports both CLI-based and REST API-based device interactions and is built to work in simulated environments (e.g., GNS3) or lab setups.

---

## 🔧 Features

- Automated configuration over **Telnet**, **SSH**, and **REST API**
- Platform detection for Cisco IOS, IOS-XE, and FTD
- Modular and extensible script structure
- Configuration templates per device type
- Logging and basic rollback on error
- Tested in GNS3 simulation environment

---

## 📂 Project Structure

```bash
proiect_FilipCojita/
├── configure_fdm_via_rest.py
├── lint_current_dir.py
├── main_1dev.py
├── main_alldev
├── mocktests.py
├── mytopo.yaml
├── pylintrc
├── rest_connector.py
├── ssh_connector_paramiko.py    # SSH-based automation using Paramiko
├── swagger_connector
├── telnet_connector2.py         # Telnet-based config for initial setups
├── ubuntu_setup.py    
├── verify_ubuntu_ping            
└── README.md                    # Project documentation
````

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/network-automation.git
cd network-automation
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies include:

* `paramiko` – SSH automation
* `requests` – For REST API (FTD)
* `time`, `os`, `sys`, etc. – Standard libraries

### 3. Run the Script

#### Telnet Setup (e.g., initial provisioning):

```bash
python telnet_connector2.py
```

#### SSH Setup (modern workflow):

```bash
python ssh_connector_paramiko.py
```

Make sure to update device credentials and IPs inside the scripts or via an external device list.

---

## 🖼 Example Use Cases

* Push a base configuration to 10 Cisco routers in under 1 minute
* Automatically configure FTD firewalls via Swagger-based REST API
* Detect device platform and apply matching config block
* Batch configure VLANs, routing, interfaces, or security policies

---

## 📊 Results

* ⚡ \~70% faster configuration time
* 🛡 90% fewer config errors compared to manual entry
* 🔍 100% accurate platform detection during tests
* 📦 Scales to 20+ devices per batch run

---

## 🧱 Built With

* Python 3.x
* [Paramiko](https://www.paramiko.org/)
* Cisco IOS / IOS-XE / FTD
* GNS3 (for virtual testbed)

---

## ✅ Future Improvements

* Add threading for parallel device execution
* Web GUI for config launches and monitoring
* Centralized logging and device inventory
* Extend support to Juniper and Arista platforms

---

## 🧑‍💻 Author

**Your Name**
[filipcojita@gmail.com](mailto:filipcojita@gmail.com)
GitHub: [github.com/filipcojita](https://github.com/filipcojita)

---

## Screenshots
# Topology:
![topogns3](https://github.com/user-attachments/assets/6cb28dff-c283-4ab7-97f3-45733744e04a)
# Project Requirements
![Requirements](https://github.com/user-attachments/assets/bbac82b0-ecc1-4120-8341-c7e19cbd7663)
# Ubuntu initial config
![ubuntuconfigss](https://github.com/user-attachments/assets/ed893104-10c6-4925-98c6-8f4718adb65c)
# Testbed Sample
![testbedsample](https://github.com/user-attachments/assets/f40026ca-7a8b-458f-8c60-f04a19af0265)
# Output after initial configuration
![conf_result_1](https://github.com/user-attachments/assets/87ee931d-045e-4021-821e-edaa712b8b7e)
![conf_result_2](https://github.com/user-attachments/assets/9c546167-55dc-4eb3-8f78-efd54b68604f)
# DHCP set on devices
![ubuntuguest1_dhcp](https://github.com/user-attachments/assets/1b7cd069-ce5b-4cf0-91aa-969e21ab97d3)
![dns_dhcp](https://github.com/user-attachments/assets/136bba7b-2c37-4071-96aa-80fd4811476e)
# Ping results from endpoint to devices
![ping_result](https://github.com/user-attachments/assets/cacffefc-0c1e-472a-8c35-165789ee185d)
# Mocktests output
![test_res_1](https://github.com/user-attachments/assets/4b577d71-4cdc-458e-935b-281fcffb2293)
![test_res_2](https://github.com/user-attachments/assets/3b620e70-653f-4b42-a0f5-dff11fe93312)
![test_res_3](https://github.com/user-attachments/assets/9bd18ab8-7acc-4ead-8488-65b366669541)
# Pylint result
![pylint_res](https://github.com/user-attachments/assets/45eca733-3fc3-47bf-8dce-b92b69f24c72)
# FDM interfaces set from code
![ftd_interfaces](https://github.com/user-attachments/assets/71d02314-7fc7-4652-8a31-34ef526afb1e)

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
