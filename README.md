# Network Documentation

Network device inventory system using NetBox IPAM, automated MAC vendor lookup, and network topology documentation for a multi-VLAN home lab.

## What This Does

1. **Network scanning** — nmap-based device discovery across the network
2. **MAC vendor identification** — Automated OUI lookup via macvendors.com API
3. **NetBox bulk import** — Python script to populate NetBox with all discovered devices, interfaces, and IP addresses
4. **Network topology** — Draw.io diagram documenting the full network layout

## Scripts

### netbox_bulk_import.py

Bulk-imports 13 network devices into NetBox via REST API. Automatically creates manufacturers, device types, interfaces (with MAC addresses), and IP assignments.

```bash
export NETBOX_TOKEN="your-netbox-api-token"
python3 scripts/netbox_bulk_import.py
```

### mac_vendor_lookup.py

Reads a device inventory CSV, looks up unknown MAC address vendors using the macvendors.com API, and writes an updated CSV with vendor information filled in.

```bash
python3 scripts/mac_vendor_lookup.py data/exports/device_inventory.csv
```

## Data

### Device Inventory

`data/exports/device_inventory.csv` — All discovered devices with IP, MAC, vendor, and device type.

### Network Scans

- `data/scans/2025-12-21_network-scan.txt` — Initial ARP/nmap scan
- `data/scans/2025-12-23_nmap-scan.txt` — Follow-up nmap scan with service detection

### Network Topology

`diagrams/network-topology.drawio` — Full network topology diagram (open with Draw.io or diagrams.net). Includes all 13 devices with IP addresses, MAC addresses, and connections.

## Network Overview

- **Gateway:** AT&T BGW320-505 (192.168.1.254)
- **Core Switch:** MikroTik CRS309-1G-8S+
- **VLANs:** Production (10), IoT (20), Management (40), Pentesting (50)
- **Devices:** 5x Raspberry Pi, workstation, PlayStation, IoT devices
- **IPAM:** NetBox (Docker) with PostgreSQL backend

## Technologies

Python, NetBox REST API, nmap, ARP scanning, Docker, PostgreSQL, Draw.io
