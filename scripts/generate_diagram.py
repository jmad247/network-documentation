#!/usr/bin/env python3
"""
Network Diagram Generator
Auto-generates network topology diagrams from inventory data
"""

import json
import argparse
from pathlib import Path

from diagrams import Diagram, Cluster, Edge
from diagrams.generic.network import Switch, Router, Firewall
from diagrams.generic.compute import Rack
from diagrams.generic.storage import Storage
from diagrams.onprem.compute import Server
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.network import Internet
from diagrams.generic.device import Mobile, Tablet


# Network inventory - can be loaded from JSON/Netbox
INVENTORY = {
    "core": {
        "name": "MikroTik CRS309",
        "type": "switch",
        "ip": "192.168.88.1",
        "ports": 10,
        "vlans": [10, 20, 30, 100]
    },
    "servers": [
        {"name": "Docker Host", "ip": "192.168.10.194", "services": ["Prometheus", "Grafana", "Netbox"]},
    ],
    "vlans": [
        {"id": 10, "name": "Management", "subnet": "192.168.10.0/24"},
        {"id": 20, "name": "Servers", "subnet": "192.168.20.0/24"},
        {"id": 30, "name": "IoT", "subnet": "192.168.30.0/24"},
        {"id": 100, "name": "Guest", "subnet": "192.168.100.0/24"},
    ],
    "monitoring": {
        "prometheus": "http://localhost:9090",
        "grafana": "http://localhost:3000",
        "alertmanager": "http://localhost:9093"
    }
}


def generate_physical_topology(output_dir: str = "diagrams"):
    """Generate physical network topology diagram"""

    with Diagram(
        "Physical Network Topology",
        filename=f"{output_dir}/physical_topology",
        show=False,
        direction="TB",
        graph_attr={"fontsize": "20", "bgcolor": "white"}
    ):
        internet = Internet("Internet")

        with Cluster("Core Infrastructure"):
            core_switch = Switch("MikroTik CRS309\n192.168.88.1")

        with Cluster("Server Rack"):
            docker_host = Server("Docker Host\n192.168.10.194")

        with Cluster("Monitoring Stack"):
            prometheus = Prometheus("Prometheus\n:9090")
            grafana = Grafana("Grafana\n:3000")

        with Cluster("End Devices"):
            workstation = Server("Workstations")
            iot = Mobile("IoT Devices")

        # Connections
        internet >> Edge(label="WAN") >> core_switch
        core_switch >> Edge(label="VLAN 10") >> docker_host
        core_switch >> Edge(label="VLAN 20") >> workstation
        core_switch >> Edge(label="VLAN 30") >> iot

        docker_host >> prometheus
        docker_host >> grafana
        prometheus >> Edge(label="SNMP", style="dashed") >> core_switch

    print(f"Generated: {output_dir}/physical_topology.png")


def generate_logical_topology(output_dir: str = "diagrams"):
    """Generate logical/VLAN topology diagram"""

    with Diagram(
        "Logical Network Topology (VLANs)",
        filename=f"{output_dir}/logical_topology",
        show=False,
        direction="LR",
        graph_attr={"fontsize": "20", "bgcolor": "white"}
    ):
        core = Switch("CRS309 Core")

        with Cluster("VLAN 10 - Management\n192.168.10.0/24"):
            mgmt_devices = [
                Server("Docker Host"),
                Server("Admin WS"),
            ]

        with Cluster("VLAN 20 - Servers\n192.168.20.0/24"):
            server_devices = [
                Server("App Server"),
                Storage("NAS"),
            ]

        with Cluster("VLAN 30 - IoT\n192.168.30.0/24"):
            iot_devices = [
                Mobile("Smart Devices"),
                Tablet("Tablets"),
            ]

        with Cluster("VLAN 100 - Guest\n192.168.100.0/24"):
            guest_devices = [
                Mobile("Guest WiFi"),
            ]

        # Connect all to core
        for device in mgmt_devices:
            core >> Edge(color="green") >> device
        for device in server_devices:
            core >> Edge(color="blue") >> device
        for device in iot_devices:
            core >> Edge(color="orange") >> device
        for device in guest_devices:
            core >> Edge(color="red", style="dashed") >> device

    print(f"Generated: {output_dir}/logical_topology.png")


def generate_monitoring_diagram(output_dir: str = "diagrams"):
    """Generate monitoring stack architecture diagram"""

    with Diagram(
        "Monitoring Architecture",
        filename=f"{output_dir}/monitoring_architecture",
        show=False,
        direction="TB",
        graph_attr={"fontsize": "20", "bgcolor": "white"}
    ):
        with Cluster("Network Devices"):
            mikrotik = Switch("MikroTik CRS309")
            endpoints = Internet("External Endpoints")

        with Cluster("Docker Host"):
            with Cluster("Exporters"):
                snmp_exp = Server("SNMP Exporter\n:9116")
                node_exp = Server("Node Exporter\n:9100")
                blackbox = Server("Blackbox\n:9115")

            with Cluster("Monitoring Core"):
                prometheus = Prometheus("Prometheus\n:9090")
                alertmanager = Server("Alertmanager\n:9093")

            with Cluster("Visualization"):
                grafana = Grafana("Grafana\n:3000")

        with Cluster("Notifications"):
            slack = Mobile("Slack")

        # Data flow
        mikrotik >> Edge(label="SNMP") >> snmp_exp
        endpoints >> Edge(label="ICMP/HTTP") >> blackbox

        snmp_exp >> prometheus
        node_exp >> prometheus
        blackbox >> prometheus

        prometheus >> alertmanager
        prometheus >> grafana
        alertmanager >> Edge(label="Webhook") >> slack

    print(f"Generated: {output_dir}/monitoring_architecture.png")


def generate_all_diagrams(output_dir: str = "diagrams"):
    """Generate all network diagrams"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("Generating network diagrams...")
    generate_physical_topology(output_dir)
    generate_logical_topology(output_dir)
    generate_monitoring_diagram(output_dir)
    print(f"\nAll diagrams saved to {output_dir}/")


def load_inventory_from_file(filepath: str) -> dict:
    """Load inventory from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Network Diagram Generator")
    parser.add_argument("--output", "-o", default="diagrams", help="Output directory")
    parser.add_argument("--type", "-t", choices=["all", "physical", "logical", "monitoring"],
                        default="all", help="Diagram type to generate")
    parser.add_argument("--inventory", "-i", help="Path to inventory JSON file")
    args = parser.parse_args()

    if args.inventory:
        global INVENTORY
        INVENTORY = load_inventory_from_file(args.inventory)

    if args.type == "all":
        generate_all_diagrams(args.output)
    elif args.type == "physical":
        generate_physical_topology(args.output)
    elif args.type == "logical":
        generate_logical_topology(args.output)
    elif args.type == "monitoring":
        generate_monitoring_diagram(args.output)


if __name__ == "__main__":
    main()
