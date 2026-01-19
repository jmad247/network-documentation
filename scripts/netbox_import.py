#!/usr/bin/env python3
"""
Netbox Import Script
Imports inventory data from JSON into Netbox via API
"""

import argparse
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class NetboxClient:
    def __init__(self, url: str, token: str):
        self.base_url = url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        url = f"{self.base_url}/api/{endpoint}"
        body = json.dumps(data).encode() if data else None

        req = Request(url, data=body, headers=self.headers, method=method)

        try:
            with urlopen(req) as response:
                return json.loads(response.read().decode())
        except HTTPError as e:
            error_body = e.read().decode()
            print(f"HTTP {e.code}: {error_body}", file=sys.stderr)
            return None

    def get(self, endpoint: str) -> dict:
        return self._request('GET', endpoint)

    def post(self, endpoint: str, data: dict) -> dict:
        return self._request('POST', endpoint, data)

    def create_site(self, name: str, slug: str = None) -> dict:
        slug = slug or name.lower().replace(' ', '-')
        return self.post('dcim/sites/', {
            'name': name,
            'slug': slug,
            'status': 'active',
        })

    def create_manufacturer(self, name: str) -> dict:
        slug = name.lower().replace(' ', '-')
        return self.post('dcim/manufacturers/', {
            'name': name,
            'slug': slug,
        })

    def create_device_type(self, manufacturer_id: int, model: str) -> dict:
        slug = model.lower().replace(' ', '-').replace('+', 'plus')
        return self.post('dcim/device-types/', {
            'manufacturer': manufacturer_id,
            'model': model,
            'slug': slug,
        })

    def create_device_role(self, name: str, color: str = '0000ff') -> dict:
        slug = name.lower().replace(' ', '-')
        return self.post('dcim/device-roles/', {
            'name': name,
            'slug': slug,
            'color': color,
        })

    def create_device(self, name: str, device_type_id: int, role_id: int, site_id: int) -> dict:
        return self.post('dcim/devices/', {
            'name': name,
            'device_type': device_type_id,
            'role': role_id,
            'site': site_id,
            'status': 'active',
        })

    def create_vlan(self, vid: int, name: str, site_id: int = None) -> dict:
        return self.post('ipam/vlans/', {
            'vid': vid,
            'name': name,
            'site': site_id,
            'status': 'active',
        })

    def create_prefix(self, prefix: str, vlan_id: int = None, description: str = '') -> dict:
        data = {
            'prefix': prefix,
            'status': 'active',
            'description': description,
        }
        if vlan_id:
            data['vlan'] = vlan_id
        return self.post('ipam/prefixes/', data)


def import_inventory(client: NetboxClient, inventory_file: str):
    """Import inventory from JSON file to Netbox"""

    with open(inventory_file, 'r') as f:
        inventory = json.load(f)

    print("Importing inventory to Netbox...")

    # Create sites
    site_map = {}
    for site in inventory.get('sites', []):
        result = client.create_site(site['name'])
        if result:
            site_map[site['name']] = result['id']
            print(f"  Created site: {site['name']}")

    # Create VLANs
    vlan_map = {}
    for vlan in inventory.get('vlans', []):
        site_id = site_map.get('Home Lab')
        result = client.create_vlan(vlan['id'], vlan['name'], site_id)
        if result:
            vlan_map[vlan['id']] = result['id']
            print(f"  Created VLAN: {vlan['id']} - {vlan['name']}")

    # Create IP prefixes
    for prefix in inventory.get('ip_prefixes', []):
        vlan_id = vlan_map.get(prefix.get('vlan'))
        result = client.create_prefix(
            prefix['prefix'],
            vlan_id,
            prefix.get('description', '')
        )
        if result:
            print(f"  Created prefix: {prefix['prefix']}")

    print("\nImport complete!")


def main():
    parser = argparse.ArgumentParser(description="Import inventory to Netbox")
    parser.add_argument("--url", default="http://localhost:8000", help="Netbox URL")
    parser.add_argument("--token", required=True, help="Netbox API token")
    parser.add_argument("--inventory", "-i", default="inventory.json", help="Inventory file")
    args = parser.parse_args()

    client = NetboxClient(args.url, args.token)

    # Test connection
    result = client.get('status/')
    if not result:
        print("Failed to connect to Netbox", file=sys.stderr)
        sys.exit(1)

    print(f"Connected to Netbox {result.get('netbox-version', 'unknown')}")

    import_inventory(client, args.inventory)


if __name__ == "__main__":
    main()
