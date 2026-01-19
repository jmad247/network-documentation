#!/usr/bin/env python3
"""
Configuration Sync Script
Pulls configs from network devices and commits to Git
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import librouteros
from librouteros import connect


# Device inventory
DEVICES = [
    {
        "name": "crs309",
        "host": "192.168.88.1",
        "username": "admin",
        "password": "",
        "type": "mikrotik"
    }
]


def connect_mikrotik(host: str, username: str, password: str, port: int = 8728):
    """Connect to MikroTik device"""
    try:
        api = connect(
            host=host,
            username=username,
            password=password,
            port=port,
        )
        return api
    except Exception as e:
        print(f"Failed to connect to {host}: {e}", file=sys.stderr)
        return None


def get_mikrotik_config(api) -> dict:
    """Get configuration sections from MikroTik"""
    config = {
        "identity": "",
        "interfaces": [],
        "vlans": [],
        "bridge_ports": [],
        "ip_addresses": [],
        "firewall_filter": [],
        "snmp": [],
    }

    # System identity
    for item in api.path("/system/identity"):
        config["identity"] = item.get("name", "unknown")

    # Interfaces
    for item in api.path("/interface"):
        config["interfaces"].append({
            "name": item.get("name"),
            "type": item.get("type"),
            "mac": item.get("mac-address"),
            "mtu": item.get("mtu"),
            "running": item.get("running"),
            "disabled": item.get("disabled"),
        })

    # VLANs
    for item in api.path("/interface/vlan"):
        config["vlans"].append({
            "name": item.get("name"),
            "vlan_id": item.get("vlan-id"),
            "interface": item.get("interface"),
            "disabled": item.get("disabled"),
        })

    # Bridge ports
    for item in api.path("/interface/bridge/port"):
        config["bridge_ports"].append({
            "interface": item.get("interface"),
            "bridge": item.get("bridge"),
            "pvid": item.get("pvid"),
            "frame_types": item.get("frame-types"),
        })

    # IP addresses
    for item in api.path("/ip/address"):
        config["ip_addresses"].append({
            "address": item.get("address"),
            "interface": item.get("interface"),
            "network": item.get("network"),
            "disabled": item.get("disabled"),
        })

    # Firewall filter
    for item in api.path("/ip/firewall/filter"):
        config["firewall_filter"].append({
            "chain": item.get("chain"),
            "action": item.get("action"),
            "src_address": item.get("src-address"),
            "dst_address": item.get("dst-address"),
            "protocol": item.get("protocol"),
            "dst_port": item.get("dst-port"),
            "comment": item.get("comment"),
            "disabled": item.get("disabled"),
        })

    # SNMP
    for item in api.path("/snmp"):
        config["snmp"].append({
            "enabled": item.get("enabled"),
            "contact": item.get("contact"),
            "location": item.get("location"),
        })

    return config


def save_config(device_name: str, config: dict, output_dir: str):
    """Save configuration to file"""
    import json

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save as JSON
    json_file = output_path / f"{device_name}.json"
    with open(json_file, 'w') as f:
        json.dump(config, f, indent=2, default=str)

    # Save as human-readable text
    txt_file = output_path / f"{device_name}.txt"
    with open(txt_file, 'w') as f:
        f.write(f"# Configuration for {device_name}\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n\n")

        f.write(f"Identity: {config['identity']}\n\n")

        f.write("## Interfaces\n")
        for iface in config['interfaces']:
            status = "UP" if iface['running'] else "DOWN"
            f.write(f"  {iface['name']}: {iface['type']} [{status}]\n")

        f.write("\n## VLANs\n")
        for vlan in config['vlans']:
            f.write(f"  VLAN {vlan['vlan_id']}: {vlan['name']} on {vlan['interface']}\n")

        f.write("\n## IP Addresses\n")
        for ip in config['ip_addresses']:
            f.write(f"  {ip['address']} on {ip['interface']}\n")

        f.write("\n## Bridge Ports\n")
        for port in config['bridge_ports']:
            f.write(f"  {port['interface']}: bridge={port['bridge']} pvid={port['pvid']}\n")

        f.write("\n## Firewall Rules\n")
        for rule in config['firewall_filter']:
            f.write(f"  {rule['chain']}: {rule['action']} - {rule.get('comment', 'no comment')}\n")

    return json_file, txt_file


def git_commit(config_dir: str, message: str):
    """Commit changes to Git"""
    try:
        # Add all config files
        subprocess.run(["git", "add", config_dir], check=True, capture_output=True)

        # Check if there are changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True
        )

        if result.returncode != 0:  # Changes exist
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True
            )
            print(f"Committed: {message}")
            return True
        else:
            print("No changes to commit")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        return False


def sync_all_devices(output_dir: str = "configs", commit: bool = True):
    """Sync configurations from all devices"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    changes = []

    for device in DEVICES:
        print(f"Syncing {device['name']} ({device['host']})...")

        if device['type'] == 'mikrotik':
            api = connect_mikrotik(
                device['host'],
                device['username'],
                device['password']
            )

            if api:
                config = get_mikrotik_config(api)
                json_file, txt_file = save_config(device['name'], config, output_dir)
                print(f"  Saved: {json_file}")
                print(f"  Saved: {txt_file}")
                changes.append(device['name'])
            else:
                print(f"  Failed to connect")

    if commit and changes:
        message = f"Config sync: {', '.join(changes)} - {timestamp}"
        git_commit(output_dir, message)

    return changes


def main():
    parser = argparse.ArgumentParser(description="Sync network device configurations")
    parser.add_argument("--output", "-o", default="configs", help="Output directory")
    parser.add_argument("--no-commit", action="store_true", help="Don't commit to Git")
    parser.add_argument("--device", "-d", help="Sync specific device only")
    args = parser.parse_args()

    if args.device:
        global DEVICES
        DEVICES = [d for d in DEVICES if d['name'] == args.device]
        if not DEVICES:
            print(f"Device '{args.device}' not found in inventory")
            sys.exit(1)

    changes = sync_all_devices(args.output, commit=not args.no_commit)

    if changes:
        print(f"\nSynced {len(changes)} device(s)")
    else:
        print("\nNo devices synced")


if __name__ == "__main__":
    main()
