# 🚀 Cloudflare DDNS
Updates Cloudflare's A records Automatically. Making it your own DDNS with our own domain name. I previously had GoDaddy update that is not available unless you have more than 10 domains in you account.
### why this project ?
I made a Cloudflare DDNS which has a Free API. If you brought your domain in other agents. you can ponint that Name servers to cloudflare and its free. 
When using the free public ddns it whant to make their DNS as your primary DNS configuration. This makes you volnurable. And the cost is pritty much high when compared to buying your domain itself. Domain cost $10 – $20/year (e.g., .com, .net). Paid DDNS $25 – $55/year (Standard Premium tiers).Not free version those have no privacy against data bokers. every thing costs money free versions get the cost back by selling your data. 
also fre versions limits to 5-10 subdomains per accounts. if you buy one domain name you get unlimited subdomains.

### Cloudflare DNS Auto-Updater for PC / local_server / AWS EC2 / Embedded remote projects
* Better if your are using the AWS instance ocassionaly. but not deleting the instance. so, when the EC2's public changes you won't be affected. other wise it will reset the Public IPv4 and It's Public DNS. check ✅ this setup will automatically updates the cloudflare records. (EC2 Elastic IP($3.65 / month), if you don't want to shut down your instances. But, I shutdown and restart every day whenever i want to use my features from my server. so, EC2 static IP is waste of money for me.)
* If your are using ISP they change the IP every 24hrs or even often sometimes. check ✅ again you get help with this one.
* a home server to access from outside ✅ check
A Python-based utility designed to run on **AWS EC2** instances (optimized for **RedHat 10.1** and **Ubuntu 24.04**) to automatically update a Cloudflare A record with the instance's public IP address upon every boot.

## 🚀 Features

* **Auto-Detection:** Automatically fetches the EC2 instance's public IPv4 address.
* **Cloudflare Integration:** Uses Cloudflare API v4 with secure Bearer Token authentication.
* **Custom TTL:** Configured for a **2-hour (7200s)** TTL to balance propagation and API overhead.
* **Self-Deploying:** Script includes logic to move itself to `/usr/local/bin/` and set appropriate permissions.
* **Systemd Ready:** Designed to trigger as a `oneshot` service after the network is online.

## 🛠 Prerequisites

1.  **Python 3.12+**
2.  python modules to install
    * `requests`
    *  `json`
    *  `logging`
4.  **Cloudflare Credentials:**
    * `ZONE_ID`: Found in your Cloudflare Domain Overview.
    * `API_TOKEN`: Created via *My Profile > API Tokens* (requires `DNS:Edit` and `Zone:Read` permissions).
    * `RECORD_NAME`: Your domain name as your wish.

## 📥 Installation

### 1. Install Dependencies
Since modern Linux distributions (PEP 668) restrict global `pip` installs, use the system package manager:

**Ubuntu:**
```bash
sudo apt update && sudo apt install python3-requests dns.resolver -y
```

## 2. Deploy and Test

Run the script once with `sudo`. This will move the script to `/usr/local/bin/update_dns.py` and attempt the first update:

```bash
sudo python3 update_dns.py
```

---

## 3. Automate on Boot

Create a `systemd` service to run the script automatically.

### Create the service file:

```bash
sudo nano /etc/systemd/system/update-dns.service
```

### Paste the following configuration:

```ini
[Unit]
Description=Update Cloudflare DNS Record on Boot
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /usr/local/bin/update_dns.py
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### Enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable update-dns.service
```

---

## 🔍 Troubleshooting

### Authentication Error (9106/6111)

Double-check that you are using an **API Token** and not a **Global API Key**.

### Permission Denied

Ensure you run the initial script and `systemctl` commands with `sudo`.

---

## 📄 License

MIT
