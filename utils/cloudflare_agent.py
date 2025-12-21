def get_cloudflare_agent():
    import os
    import requests
    from dotenv import load_dotenv

    load_dotenv()

    # Add a check for missing environment variables
    if not os.getenv("CF_API_KEY"):
        raise ValueError("Missing required environment variable: CF_API_KEY")

    api_key = os.getenv("CF_API_KEY")

    # Updated headers for Bearer token authentication
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    return headers, requests


def get_all_zones():
    headers, requests = get_cloudflare_agent()
    url = "https://api.cloudflare.com/client/v4/zones"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("result", [])
    else:
        print(f"Error fetching zones: {response.status_code}", response.text)
        return []

# Functions
def update_records(old_ip, new_ip):
    headers, requests = get_cloudflare_agent()
    zones = get_all_zones()
    
    if not zones:
        print("No zones found in Cloudflare account")
        return False
    
    total_errors = 0
    total_updated = 0
    
    # Loop through all zones
    for zone in zones:
        zone_id = zone['id']
        zone_name = zone['name']
        print(f"\n=== Checking zone: {zone_name} ===")
        
        update_list = []
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # Check all records for the old IP
            for record in data.get("result", []):
                # Save the record if it matches the old IP and prepare it for update with the new IP
                if record['type'] == 'A' and record['content'] == old_ip:
                    update_record = {
                        "id": record['id'],
                        "zone_id": zone_id,
                        "data": {
                        "content": new_ip,
                        "name": record['name'],
                        "proxied": record['proxied'],
                        "ttl": record['ttl'],
                        "type": record['type']
                        }
                    }
                    update_list.append(update_record)
                    print(f"Found record with old IP:")
                    print(f"ID: {record['id']}\nName: {record['name']}\nType: {record['type']}\nContent: {record['content']}\n")
        else:
            print(f"Error fetching records for zone {zone_name}: {response.status_code}", response.text)
            total_errors += 1
            continue

        # Update each saved record with the new IP
        for record_data in update_list:
            update_url = f"https://api.cloudflare.com/client/v4/zones/{record_data['zone_id']}/dns_records/{record_data['id']}"
            response = requests.put(update_url, headers=headers, json=record_data['data'])
            print(f"Cloudflare response:")
            print(response.json())
            if response.status_code == 200:
                print(f"Cloudflare Record {record_data['data']['name']} updated to {new_ip} successfully!")
                total_updated += 1
            else:
                print(f"Error updating record {record_data['data']['name']}")
                total_errors += 1
    
    print(f"\n=== Summary: Updated {total_updated} records across all zones ===")
    
    if total_errors > 0:
        return False
    else:
        return True


# Firewall Access Rules Functions
def list_access_rules():
    headers, requests = get_cloudflare_agent()
    
    # First, get the account ID from zones
    zones = get_all_zones()
    if not zones:
        print("No zones found")
        return []
    
    # Get account_id from the first zone
    account_id = zones[0].get('account', {}).get('id')
    if not account_id:
        print("Could not retrieve account ID")
        return []
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/firewall/access_rules/rules"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("result", [])
    else:
        print(f"Error fetching access rules: {response.status_code}", response.text)
        return []


def delete_access_rule(rule_id):
    headers, requests = get_cloudflare_agent()
    zones = get_all_zones()
    if not zones:
        return False
    
    account_id = zones[0].get('account', {}).get('id')
    if not account_id:
        return False
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/firewall/access_rules/rules/{rule_id}"
    
    response = requests.delete(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        print(f"Error deleting access rule: {response.status_code}", response.text)
        return False


def create_access_rule(new_ip, mode="whitelist", notes=None):
    headers, requests = get_cloudflare_agent()
    zones = get_all_zones()
    if not zones:
        return False
    
    account_id = zones[0].get('account', {}).get('id')
    if not account_id:
        return False
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/firewall/access_rules/rules"
    
    data = {
        "configuration": {
            "target": "ip",
            "value": new_ip
        },
        "mode": mode
    }
    
    if notes:
        data["notes"] = notes
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return True
    else:
        print(f"Error creating access rule: {response.status_code}", response.text)
        return False


def update_access_rule(rule_id, new_ip, mode="whitelist", notes=None):
    # Delete the old rule
    if not delete_access_rule(rule_id):
        return False
    
    # Create new rule with updated IP
    if create_access_rule(new_ip, mode, notes):
        print(f"Firewall access rule recreated with IP {new_ip} successfully!")
        return True
    else:
        print(f"Error recreating access rule with {new_ip}")
        return False


def update_firewall_rules(old_ip, new_ip):
    print("\n=== Checking Firewall Access Rules ===")
    rules = list_access_rules()
    
    if not rules:
        print("No firewall access rules found")
        return True
    
    rules_to_update = []
    for rule in rules:
        config = rule.get('configuration', {})
        if config.get('target') == 'ip' and config.get('value') == old_ip:
            rules_to_update.append(rule)
            print(f"Found firewall rule to update:")
            print(f"ID: {rule['id']}\nMode: {rule['mode']}\nIP: {config['value']}\nNotes: {rule.get('notes', 'N/A')}\n")
    
    if not rules_to_update:
        print(f"No firewall rules matching {old_ip} found")
        return True
    
    total_errors = 0
    total_updated = 0
    
    for rule in rules_to_update:
        mode = rule.get('mode', 'whitelist')
        notes = rule.get('notes')
        if update_access_rule(rule['id'], new_ip, mode, notes):
            total_updated += 1
        else:
            total_errors += 1
    
    print(f"\n=== Summary: Updated {total_updated} firewall access rules ===")
    
    return total_errors == 0