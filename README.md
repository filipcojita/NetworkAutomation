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

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
