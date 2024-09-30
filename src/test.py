import os
import json

# The line to add
alloc_data = {
    "alloc": {
        "f17f52151EbEF6C7334FAD080c5704D77216b732": {"balance": "1000000000000000000000000000"},
        "627306090abaB3A6e1400e9345bC60c78a8BEf57": {"balance": "1000000000000000000000000000"},
        "fe3b557e8fb62b89f4916b721be55ceb828dbd73": {"balance": "1000000000000000000000000000"}
    }
}

# Read the genesis.json file
with open('genesis.json', 'r') as f:
    genesis_data = json.load(f)

# Add the alloc data after the extraData key
genesis_data["alloc"] = alloc_data["alloc"]

# Write the modified content back to the genesis.json file
with open('genesis.json', 'w') as f:
    json.dump(genesis_data, f, indent=4)

print("Alloc data added to genesis.json")