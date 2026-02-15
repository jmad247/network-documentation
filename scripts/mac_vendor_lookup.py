#!/usr/bin/env python3
"""
MAC Vendor Lookup Tool
Queries online MAC vendor databases to identify device manufacturers
"""

import requests
import time
import csv
import sys
from pathlib import Path

# MAC Vendor API endpoints
MAC_VENDORS_API = "https://api.macvendors.com/"

def lookup_mac_vendor(mac_address):
    """
    Lookup MAC vendor using macvendors.com API
    Free tier: 1 request per second

    Args:
        mac_address: MAC address in any format

    Returns:
        Vendor name or "Unknown"
    """
    try:
        response = requests.get(f"{MAC_VENDORS_API}{mac_address}", timeout=5)

        if response.status_code == 200:
            return response.text.strip()
        elif response.status_code == 404:
            # Check if locally administered MAC
            if is_locally_administered(mac_address):
                return "Locally Administered"
            return "Unknown"
        else:
            return f"Error: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def is_locally_administered(mac_address):
    """
    Check if MAC address is locally administered
    Bit 1 of first octet indicates local administration
    """
    # Remove common delimiters
    mac_clean = mac_address.replace(':', '').replace('-', '').replace('.', '')

    if len(mac_clean) < 2:
        return False

    # Get first octet
    first_octet = int(mac_clean[0:2], 16)

    # Check bit 1 (locally administered bit)
    return bool(first_octet & 0x02)

def process_inventory_file(input_file, output_file):
    """
    Read device inventory CSV, lookup unknown vendors, write updated file
    """
    devices = []
    unknown_count = 0
    updated_count = 0

    print(f"Reading inventory from: {input_file}")

    # Read existing inventory
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        devices = list(reader)

    print(f"Found {len(devices)} devices")
    print("Lookup up unknown vendors...")
    print("-" * 60)

    # Process each device
    for device in devices:
        mac = device['MAC Address']
        current_vendor = device['Vendor']

        if current_vendor == "Unknown" or not current_vendor:
            unknown_count += 1
            print(f"Looking up {mac}...", end=" ")

            vendor = lookup_mac_vendor(mac)
            device['Vendor'] = vendor

            if vendor != "Unknown":
                updated_count += 1
                print(f"✓ {vendor}")
            else:
                print("✗ Still unknown")

            # Rate limiting: 1 request per second
            time.sleep(1.1)
        else:
            print(f"Skipping {mac} - already has vendor: {current_vendor}")

    print("-" * 60)
    print(f"Lookup complete:")
    print(f"  - Total unknown: {unknown_count}")
    print(f"  - Successfully identified: {updated_count}")
    print(f"  - Still unknown: {unknown_count - updated_count}")

    # Write updated inventory
    print(f"\nWriting updated inventory to: {output_file}")

    with open(output_file, 'w', newline='') as f:
        fieldnames = devices[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(devices)

    print("Done!")

def main():
    """Main entry point"""
    # Default file paths
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data/exports/device_inventory.csv"
    output_file = project_root / "data/exports/device_inventory_updated.csv"

    # Allow override from command line
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    process_inventory_file(input_file, output_file)

if __name__ == "__main__":
    main()
