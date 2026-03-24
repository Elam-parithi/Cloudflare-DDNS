
import sys
import os
# Forces the buffer to flush on every write
sys.stdout.reconfigure(line_buffering=True)

import requests
import json
import socket
import dns.resolver
import time
import logging
from logging.handlers import WatchedFileHandler

# --- Configuration ---
API_TOKEN = "YOUR_CLOUDFLARE_API_TOKEN"
ZONE_ID = "YOUR_ZONE_ID"
RECORD_NAME = "YOUR_DOMAIN_ADDRESS"

# --- Logging Setup ---
LOG_FILE = "./z_dns_update.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logger = logging.getLogger() # This gets the root logger
logger.setLevel(logging.INFO)
file_handler = WatchedFileHandler(LOG_FILE)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

print("Logging initialized. All actions will be logged to z_dns_update.log`")
def get_public_ip():
    # Fetch public IP from AWS metadata service
    return requests.get("https://checkip.amazonaws.com").text.strip()
   
def lookup_dns(hostname):
    """
    Returns the IPv4 address for a given hostname.
    """
    try:
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror:
        # gaierror handles 'getaddrinfo' errors (e.g., hostname not found)
        return f"Error: Hostname '{hostname}' could not be resolved."

def lookup_at_source(hostname):
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['1.1.1.1'] # Force Cloudflare's DNS
        answer = resolver.resolve(hostname, 'A')
        return answer[0].to_text()
    except dns.resolver.NXDOMAIN:
        # THIS IS THE PART YOU WANTED: If it doesn't exist, create it.
        logging.info(f"[!] {RECORD_NAME} not found. Triggering creation...")
        new_id = create_cloudflare_record(get_public_ip())
    except Exception as e:
        logging.error(f"Unexpected error: {e}")



def create_cloudflare_record( ip_address):
    """
    Creates a new A record in Cloudflare with a timestamped comment.
    """
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    # Create the timestamp for the comment
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "type": "A",
        "name": RECORD_NAME,
        "content": ip_address,
        "ttl": 60,         # 1 minute for fast updates
        "proxied": False,  # Set to True if you want Cloudflare's CDN/Proxy
        "comment": f"Created by EC2 boot script on {current_time}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        if result.get("success"):
            logging.info(f"[+] Successfully created record: {RECORD_NAME} -> {ip_address}")
            return result["result"]["id"] # Returns the new Record ID
        else:
            logging.error(f"[!] Cloudflare Error: {result['errors']}")
            return None
            
    except Exception as e:
        logging.error(f"[!] Request failed: {e}")
        return None
    
def update_cloudflare(ip):
    DNS_TTL = 60 # seconds
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. Search for ALL records with this name
    search_url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?name={RECORD_NAME}"
    records = requests.get(search_url, headers=headers).json().get("result", [])

    if not records:
        # If no record exists at all, create one (POST)
        logging.info(f"[*] No record found for {RECORD_NAME}. Creating new one...")
        create_url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
        data = {
            "type": "A", 
            "name": RECORD_NAME, 
            "content": ip, 
            "ttl": DNS_TTL, 
            "proxied": False, 
            "comment": "Auto-updated by script@bai(update-dns.py)"+time.strftime("%Y-%m-%d %H:%M:%S")
            }
        requests.post(create_url, headers=headers, json=data)
        logging.info(f"[+] Created: {RECORD_NAME} -> {ip}")
        return

    # 2. If multiple records exist, delete the extras
    # We keep the first one and delete the rest
    main_record = records[0]
    if len(records) > 1:
        logging.info(f"[!] Found {len(records)} duplicate records. Cleaning up...")
        for extra in records[1:]:
            del_url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{extra['id']}"
            requests.delete(del_url, headers=headers)
            logging.info(f"[-] Deleted duplicate ID: {extra['id']}")

    # 3. Update the remaining main record with the new IP (PUT)
    update_url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{main_record['id']}"
    data = {
        "type": "A", 
        "name": RECORD_NAME, 
        "content": ip, 
        "ttl": DNS_TTL, 
        "proxied": False,
        "comment": "previous duplicate deleted - Auto-updated by script@bai(update-dns.py)"+time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    response = requests.put(update_url, headers=headers, json=data).json()
    
    if response.get("success"):
        logging.info(f"[+] Successfully synced {RECORD_NAME} to {ip}")
    else:
        logging.error(f"[!] Update failed: {response}")

if __name__ == "__main__":
    Okwaiting_delay = 60 # seconds
    Updateing_delay = 120 # seconds
    
    logging.info("Starting DNS update script... @ bai(update-dns.py)" + time.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info(f"Current public IP: {get_public_ip()}")
    logging.info(f"waiting delay is set to {Okwaiting_delay} seconds, update delay is set to {Updateing_delay} seconds. @main")
    print("Entering main loop. Will check every 60 seconds for IP changes...")
    while True:
        current_ip_address = get_public_ip()
        if current_ip_address is None: # if the own server ip is not available, exit with error
            logging.error("Could not retrieve own public IP address.")
        else:  # if the own server ip is available, check if it matches the current DNS record
            local_dns_recorded = lookup_dns(RECORD_NAME)
            if local_dns_recorded == current_ip_address: # checks with own DNS server
                pass
            else:
                if "Error" in local_dns_recorded:
                    logging.error(f"LOCAL DNS : NOT UPDATED [!] Error occurred while looking up local DNS: {local_dns_recorded}")
                else:
                    logging.info(f"{RECORD_NAME} => {local_dns_recorded} is outdated. {current_ip_address} is the new one.")
                # cloud flare checking area
                from_cloudflare = lookup_at_source(RECORD_NAME)
                if from_cloudflare == current_ip_address: # check with colud flare's DNS server
                    logging.info(f"CLOUDFLARE DNS : UP TO DATE | {RECORD_NAME} => {from_cloudflare} is already up to date at source(1.1.1.1). will wait for update to propagate to local DNS. waithing...(120)@source ok")
                    time.sleep(Updateing_delay) # Wait for 2 minutes to allow DNS propagation before the next check.
                else:
                    logging.info(f"CLOUDFLARE DNS : NOT UPDATED | Updating(update_cloudflare) {RECORD_NAME} => {from_cloudflare} >>>> {current_ip_address}")
                    result = update_cloudflare(current_ip_address)
                    if result is not None and result.get("success"):
                        logging.info(f"CLOUDFLARE DNS : SUCCESS | updated {RECORD_NAME} to {current_ip_address}. waithing...(90)@update")
                        time.sleep(Updateing_delay) # Wait a bit before the next check to avoid hitting before the dns record is fully propagated.
                        continue
                    else:
                        logging.error(f"Failed to update: {result}")
        logging.info("UPDATE_DNS :  OK & RUNNING | Waiting for the next check... (60 seconds)@while last")
        time.sleep(Okwaiting_delay) # Check every 1 minute
