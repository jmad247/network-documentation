#!/usr/bin/env python3
"""
NetBox Bulk Device Import Script
Imports all discovered devices into NetBox
"""

import os
import requests
import json
from pathlib import Path

# NetBox Configuration
NETBOX_URL = "http://localhost:8000"
NETBOX_TOKEN = os.environ.get("NETBOX_TOKEN", "YOUR_TOKEN_HERE")
HEADERS = {
    "Authorization": f"Token {NETBOX_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Site slug (NetBox auto-generates lowercase slug from name)
SITE_SLUG = "home-network"

def get_or_create_site(site_slug):
    """Get site ID or create if doesn't exist"""
    # Try to get existing site
    response = requests.get(
        f"{NETBOX_URL}/api/dcim/sites/?slug={site_slug}",
        headers=HEADERS
    )

    if response.status_code == 200:
        results = response.json()['results']
        if results:
            print(f"✓ Found site: {site_slug}")
            return results[0]['id']

    print(f"Site '{site_slug}' not found. Please create it in NetBox first.")
    return None

def get_or_create_manufacturer(name):
    """Get manufacturer ID by name, create if doesn't exist"""
    # Try to get existing manufacturer (use params for proper URL encoding)
    response = requests.get(
        f"{NETBOX_URL}/api/dcim/manufacturers/",
        headers=HEADERS,
        params={"name": name}
    )

    if response.status_code == 200:
        results = response.json()['results']
        if results:
            return results[0]['id']

    # Create manufacturer if not found
    print(f"  → Creating manufacturer: {name}")
    # Generate valid slug (only letters, numbers, underscores, hyphens)
    import re
    slug = re.sub(r'[^a-z0-9-_]', '', name.lower().replace(" ", "-"))
    create_response = requests.post(
        f"{NETBOX_URL}/api/dcim/manufacturers/",
        headers=HEADERS,
        json={"name": name, "slug": slug}
    )

    if create_response.status_code == 201:
        return create_response.json()['id']
    else:
        print(f"  ✗ Failed to create manufacturer: {create_response.text}")
        return None

def get_or_create_device_type(manufacturer_name, model):
    """Get device type ID, create if doesn't exist"""
    # Get or create manufacturer first
    mfr_id = get_or_create_manufacturer(manufacturer_name)
    if not mfr_id:
        print(f"  ✗ Failed to get/create manufacturer: {manufacturer_name}")
        return None

    # Try to get existing device type
    response = requests.get(
        f"{NETBOX_URL}/api/dcim/device-types/?manufacturer_id={mfr_id}&model={model}",
        headers=HEADERS
    )

    if response.status_code == 200:
        results = response.json()['results']
        if results:
            return results[0]['id']

    # Create device type if not found
    print(f"  → Creating device type: {manufacturer_name} {model}")
    slug = f"{manufacturer_name}-{model}".lower().replace(" ", "-").replace(".", "-")
    create_response = requests.post(
        f"{NETBOX_URL}/api/dcim/device-types/",
        headers=HEADERS,
        json={
            "manufacturer": mfr_id,
            "model": model,
            "slug": slug
        }
    )

    if create_response.status_code == 201:
        return create_response.json()['id']
    else:
        print(f"  ✗ Failed to create device type: {create_response.text}")
        return None

def get_device_role_id(name):
    """Get device role ID by name"""
    response = requests.get(
        f"{NETBOX_URL}/api/dcim/device-roles/?name={name}",
        headers=HEADERS
    )

    if response.status_code == 200:
        results = response.json()['results']
        if results:
            return results[0]['id']
    return None

def device_exists(device_name, site_id):
    """Check if device already exists"""
    response = requests.get(
        f"{NETBOX_URL}/api/dcim/devices/?name={device_name}&site_id={site_id}",
        headers=HEADERS
    )

    if response.status_code == 200:
        results = response.json()['results']
        if results:
            return results[0]  # Return existing device
    return None

def create_device(device_data):
    """Create a device in NetBox"""
    response = requests.post(
        f"{NETBOX_URL}/api/dcim/devices/",
        headers=HEADERS,
        json=device_data
    )

    if response.status_code == 201:
        return response.json()
    else:
        print(f"  Error creating device: {response.status_code}")
        print(f"  {response.text}")
        return None

def add_interface(device_id, interface_name, mac_address):
    """Add interface to device"""
    interface_data = {
        "device": device_id,
        "name": interface_name,
        "type": "other",
        "mac_address": mac_address.upper()
    }

    response = requests.post(
        f"{NETBOX_URL}/api/dcim/interfaces/",
        headers=HEADERS,
        json=interface_data
    )

    if response.status_code == 201:
        return response.json()
    else:
        print(f"  Warning: Could not add interface: {response.text}")
        return None

def add_ip_address(interface_id, ip_address):
    """Add IP address to interface"""
    ip_data = {
        "address": f"{ip_address}/24",
        "assigned_object_type": "dcim.interface",
        "assigned_object_id": interface_id,
        "status": "active"
    }

    response = requests.post(
        f"{NETBOX_URL}/api/ipam/ip-addresses/",
        headers=HEADERS,
        json=ip_data
    )

    if response.status_code == 201:
        return response.json()
    else:
        print(f"  Warning: Could not add IP: {response.text}")
        return None

def main():
    """Main import process"""
    print("=" * 70)
    print("NetBox Bulk Device Import")
    print("=" * 70)

    # Get site ID
    site_id = get_or_create_site(SITE_SLUG)
    if not site_id:
        print("ERROR: Could not find site. Please create 'Home Network' site first.")
        return

    # Device definitions
    devices = [
        {
            "name": "Gateway-ATT-BGW320",
            "manufacturer": "AT&T",
            "model": "BGW320",
            "role": "Gateway",
            "ip": "192.168.1.254",
            "mac": "40:e1:e4:24:31:82"
        },
        {
            "name": "Workstation-MSI",
            "manufacturer": "MicroStarInternational",
            "model": "Desktop PC",
            "role": "Workstation",
            "ip": "192.168.1.83",
            "mac": "d8:43:ae:c1:59:cb"
        },
        {
            "name": "RaspberryPi-1",
            "manufacturer": "Raspberry Pi",
            "model": "Raspberry Pi",
            "role": "Server",
            "ip": "192.168.1.79",
            "mac": "2c:cf:67:de:a2:6c"
        },
        {
            "name": "RaspberryPi-2",
            "manufacturer": "Raspberry Pi",
            "model": "Raspberry Pi",
            "role": "Server",
            "ip": "192.168.1.80",
            "mac": "2c:cf:67:de:ae:8f"
        },
        {
            "name": "RaspberryPi-3",
            "manufacturer": "Raspberry Pi",
            "model": "Raspberry Pi",
            "role": "Server",
            "ip": "192.168.1.81",
            "mac": "2c:cf:67:de:b2:e9"
        },
        {
            "name": "RaspberryPi-4",
            "manufacturer": "Raspberry Pi",
            "model": "Raspberry Pi",
            "role": "Server",
            "ip": "192.168.1.87",
            "mac": "2c:cf:67:1f:19:44"
        },
        {
            "name": "RaspberryPi-5",
            "manufacturer": "Raspberry Pi",
            "model": "Raspberry Pi",
            "role": "Server",
            "ip": "192.168.1.235",
            "mac": "d8:3a:dd:58:6b:c8"
        },
        {
            "name": "Chamberlain-myQ",
            "manufacturer": "Generic",
            "model": "Network Device",
            "role": "IOT Device",
            "ip": "192.168.1.86",
            "mac": "cc:6a:10:04:a9:32"
        },
        {
            "name": "Samsung-Device",
            "manufacturer": "Generic",
            "model": "Network Device",
            "role": "Mobile",
            "ip": "192.168.1.88",
            "mac": "00:7c:2d:35:ef:5d"
        },
        {
            "name": "PlayStation",
            "manufacturer": "Generic",
            "model": "Network Device",
            "role": "Gaming",
            "ip": "192.168.1.94",
            "mac": "bc:33:29:24:9a:e0"
        },
        {
            "name": "Atheros-Device",
            "manufacturer": "Generic",
            "model": "Network Device",
            "role": "IOT Device",
            "ip": "192.168.1.75",
            "mac": "00:03:7f:fc:e1:71"
        },
        {
            "name": "Virtual-Device-1",
            "manufacturer": "Generic",
            "model": "Network Device",
            "role": "Server",
            "ip": "192.168.1.64",
            "mac": "0e:12:3b:47:d1:57"
        },
        {
            "name": "Virtual-Device-2",
            "manufacturer": "Generic",
            "model": "Network Device",
            "role": "Server",
            "ip": "192.168.1.65",
            "mac": "ea:4d:08:b8:58:1f"
        }
    ]

    print(f"\nImporting {len(devices)} devices...")
    print("-" * 70)

    success_count = 0

    for device in devices:
        print(f"\n[{devices.index(device) + 1}/{len(devices)}] {device['name']} ({device['ip']})")

        # Check if device already exists
        existing_device = device_exists(device['name'], site_id)
        if existing_device:
            device_id = existing_device['id']
            print(f"  ⚠ Device already exists (ID: {device_id}), skipping creation")
            success_count += 1
            continue

        # Get or create device type
        device_type_id = get_or_create_device_type(device['manufacturer'], device['model'])
        if not device_type_id:
            print(f"  ✗ Skipping - failed to get/create device type")
            continue

        # Get device role ID
        role_id = get_device_role_id(device['role'])
        if not role_id:
            print(f"  ✗ Skipping - role not found: {device['role']}")
            continue

        # Create device
        device_data = {
            "name": device['name'],
            "device_type": device_type_id,
            "role": role_id,
            "site": site_id,
            "status": "active"
        }

        created_device = create_device(device_data)
        if not created_device:
            print(f"  ✗ Failed to create device")
            continue

        device_id = created_device['id']
        print(f"  ✓ Device created (ID: {device_id})")

        # Add interface
        interface = add_interface(device_id, "eth0", device['mac'])
        if interface:
            interface_id = interface['id']
            print(f"  ✓ Interface added (MAC: {device['mac']})")

            # Add IP address
            ip = add_ip_address(interface_id, device['ip'])
            if ip:
                print(f"  ✓ IP address added ({device['ip']})")
                success_count += 1
            else:
                print(f"  ✗ IP address failed")
        else:
            print(f"  ✗ Interface creation failed")

    print("\n" + "=" * 70)
    print(f"Import Complete: {success_count}/{len(devices)} devices successfully imported")
    print("=" * 70)
    print(f"\nView devices at: {NETBOX_URL}/dcim/devices/")

if __name__ == "__main__":
    main()
