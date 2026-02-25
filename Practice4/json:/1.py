import json
# Open the JSON file
with open("sample-data.json", "r") as file:
    data = json.load(file)
print("Interface Status")
print("=" * 80)
print(f"{'DN':50} {'Description':20} {'Speed':8} {'MTU':6}")
print("-" * 80)
# Access the list of interfaces (Cisco ACI-like structure)
interfaces = data["imdata"]
for item in interfaces:
    # Get interface attributes
    attributes = item["l1PhysIf"]["attributes"]
    # Extract required fields
    dn = attributes.get("dn", "")
    descr = attributes.get("descr", "")
    speed = attributes.get("speed", "")
    mtu = attributes.get("mtu", "")
    # Print formatted output
    print(f"{dn:50} {descr:20} {speed:8} {mtu:6}")