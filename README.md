# Network Documentation as Code

Automated network documentation with version control, Netbox IPAM, and auto-generated diagrams.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Documentation Pipeline                        │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   Network    │───▶│    Config    │───▶│       Git        │  │
│  │   Devices    │    │    Sync      │    │   Repository     │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                                         │             │
│         ▼                                         ▼             │
│  ┌──────────────┐                        ┌──────────────────┐  │
│  │    Netbox    │◀───────────────────────│    Diagrams      │  │
│  │    IPAM      │                        │    Generator     │  │
│  └──────────────┘                        └──────────────────┘  │
│                                                   │             │
│                                                   ▼             │
│                                          ┌──────────────────┐  │
│                                          │   PNG/SVG        │  │
│                                          │   Diagrams       │  │
│                                          └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Configuration Version Control**: Auto-pull configs from devices, commit to Git
- **Netbox IPAM**: Centralized inventory, IP management, documentation
- **Auto-Generated Diagrams**: Python-based topology diagrams from inventory
- **JSON Inventory**: Machine-readable network inventory

## Directory Structure

```
network-documentation/
├── docker-compose.yml       # Netbox stack
├── inventory.json           # Network inventory
├── scripts/
│   ├── generate_diagram.py  # Diagram generator
│   ├── sync_configs.py      # Config sync to Git
│   └── netbox_import.py     # Import to Netbox
├── configs/                  # Device configurations
├── diagrams/                 # Generated diagrams
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install diagrams librouteros
```

### 2. Generate Network Diagrams

```bash
# Generate all diagrams
python scripts/generate_diagram.py

# Generate specific diagram
python scripts/generate_diagram.py --type physical
python scripts/generate_diagram.py --type logical
python scripts/generate_diagram.py --type monitoring
```

Output: `diagrams/*.png`

### 3. Sync Device Configurations

```bash
# Sync all devices to configs/
python scripts/sync_configs.py

# Sync without Git commit
python scripts/sync_configs.py --no-commit

# Sync specific device
python scripts/sync_configs.py --device crs309
```

### 4. Deploy Netbox (Optional)

```bash
# Start Netbox stack
docker compose up -d

# Access at http://localhost:8000
# Login: admin / admin
```

### 5. Import to Netbox

```bash
# Get API token from Netbox UI (Admin > API Tokens)
python scripts/netbox_import.py --token YOUR_API_TOKEN --inventory inventory.json
```

## Diagram Types

### Physical Topology
Shows physical connections between devices, ports, and cable paths.

### Logical Topology
Shows VLAN segmentation, subnet assignments, and traffic flow.

### Monitoring Architecture
Shows the monitoring stack components and data flow.

## Inventory Format

The `inventory.json` file contains:

```json
{
  "sites": [...],
  "devices": [...],
  "vlans": [...],
  "ip_prefixes": [...]
}
```

Edit this file to reflect your network, then regenerate diagrams.

## Automation

### Scheduled Config Sync (cron)

```bash
# Sync configs daily at 2 AM
0 2 * * * cd /path/to/network-documentation && python scripts/sync_configs.py
```

### Pre-commit Hook

```bash
# Regenerate diagrams before commit
#!/bin/sh
python scripts/generate_diagram.py
git add diagrams/
```

## Integration with Other Projects

This project integrates with:

- **[network-automation](https://github.com/jmad247/network-automation)**: Uses same device inventory
- **[network-monitoring](https://github.com/jmad247/network-monitoring)**: Documents monitoring architecture

## Skills Demonstrated

- **Documentation as Code**: Version-controlled network documentation
- **Python Automation**: Custom tooling for diagram generation
- **IPAM/DCIM**: Netbox for inventory management
- **Git Workflows**: Automated config versioning
- **API Integration**: Netbox API, RouterOS API

## Generated Diagrams

After running `generate_diagram.py`:

- `diagrams/physical_topology.png` - Physical network layout
- `diagrams/logical_topology.png` - VLAN and subnet design
- `diagrams/monitoring_architecture.png` - Monitoring stack

---

**Author**: Madison
**Created**: January 2026
**License**: MIT
