import os
import subprocess
import signal
import time
import json

# Grafana default user and password: admin;admin. New password for project: hyperledger

# Script for hyperledger besu permissioned test network creation

def setup_data(numNodes=4):
    # 1. Create genesis file

    # Remove existing genesis file
    try:
        os.system('rm -rf genesis.json')
    except:
        pass

    # Remove networkFiles folder if it already exists
    try:
        os.system('rm -rf networkFiles')
    except:
        pass

    # Remove all files that start with "hotspot"
    try:
        os.system('rm -rf hotspot*')
    except:
        pass

    command = "besu operator generate-blockchain-config --config-file=ibftConfigFile.json --to=networkFiles --private-key-file-name=key"

    os.system(command)

    # This generates a folder networkFiles, copy the genesis,json inside of it and place it on the workspace
    os.system('cp networkFiles/genesis.json genesis.json')

    # Associate a balance to each address insidethe genesis.json file

    addresses = [
        "fe3b557e8fb62b89f4916b721be55ceb828dbd73",
        "627306090abaB3A6e1400e9345bC60c78a8BEf57",
        "f17f52151EbEF6C7334FAD080c5704D77216b732"
    ]

    alloc_data = {
        "alloc": {
            addresses[0]: {"balance": "1000000000000000000000000000"},
            addresses[1]: {"balance": "1000000000000000000000000000"},
            addresses[2]: {"balance": "1000000000000000000000000000"}
        }
    }


    # Add the line to the genesis.json file at the end of it, after the key closing parethesis of extraData key
    
    # Read the genesis.json file
    with open('genesis.json', 'r') as f:
        genesis_data = json.load(f)

    # Add the alloc data after the extraData key
    genesis_data["alloc"] = alloc_data["alloc"]

    # Write the modified content back to the genesis.json file
    with open('genesis.json', 'w') as f:
        json.dump(genesis_data, f, indent=4)

    # 2. create node folders

    # Remove existing folders
    for i in range(numNodes):
        try:
            os.system(f'rm -rf nodes/{i+1}')
        except:
            pass 

    for i in range(numNodes):
        os.mkdir(f'nodes/{i+1}')
        os.mkdir(f'nodes/{i+1}/data')
        
        # Copy permissions_config.toml into all data folders
        os.system(f'cp ./src/permissions_config.toml nodes/{i+1}/data') 
        
    # 3. Now add private keys, inside networkFiles theres "keys" folder and there are numNodes keys with folders that have random names that start with 0x and inside of them there are key files, assign each key in order to each node by saving both "key" and "key.pub" files on the node/data folder

    # Get all the keys
    keys_folders = os.listdir('networkFiles/keys')

    for i in range(numNodes):
        # Copy the key and key.pub files to the node/data folder
        os.system(f'cp networkFiles/keys/{keys_folders[i]}/key nodes/{i+1}/data')
        os.system(f'cp networkFiles/keys/{keys_folders[i]}/key.pub nodes/{i+1}/data')

    # Remove networkFiles folder as we no longer need it after this
    try:
        os.system('rm -rf networkFiles')
    except:
        pass

def kill_process_on_port(port):
    try:
        # Find the process ID (PID) using the port
        result = subprocess.run(
            ["lsof", "-i", f":{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in result.stdout.splitlines():
            if "LISTEN" in line:
                parts = line.split()
                pid = int(parts[1])
                # Kill the process
                os.kill(pid, signal.SIGKILL)
                print(f"Killed process {pid} on port {port}")
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")

def start_node(node_id, first_p2p_port=30303, first_rpc_http_port=8545, first_metrics_port=9545, metrics_host="0.0.0.0"):   
    print(f"\nStarting node {node_id+1}")
    # Kill processes running on the ports we require
    kill_process_on_port(first_p2p_port + node_id)
    kill_process_on_port(first_rpc_http_port + node_id)
     
    command = "besu --data-path=nodes/" + str(node_id+1) + "/data --genesis-file=genesis.json --permissions-nodes-config-file-enabled --permissions-accounts-config-file-enabled --rpc-http-enabled --rpc-http-api=ADMIN,ETH,NET,PERM,IBFT --host-allowlist=\"*\" --rpc-http-cors-origins=\"*\" --p2p-port=" + str(first_p2p_port + node_id) + " --rpc-http-port=" + str(first_rpc_http_port + node_id) + " --metrics-enabled=true --metrics-port=" + str(first_metrics_port + node_id) + f" --metrics-host={metrics_host}"
    
    # Open a new terminal window and run the command
    terminal_command = f"gnome-terminal --title='Node {node_id+1}' -- bash -c '{command}; exec bash'"
    process = subprocess.Popen(terminal_command, shell=True)
    print(f"Started node {node_id+1} in a new terminal")
    return process

def add_enode_urls(enode_urls, first_rpc_port, node_id):
    localhost_with_port = f"http://127.0.0.1:{first_rpc_port+node_id}"
    enode_urls_str = ', '.join([f'"{url}"' for url in enode_urls])
    command = f'curl -X POST --data \'{{"jsonrpc":"2.0","method":"perm_addNodesToAllowlist","params":[[{enode_urls_str}]], "id":1}}\' {localhost_with_port}'
    
    print(f"\n\nAdding enode URLs for node {node_id+1}:")
    print(command)
    
    # Run command and print output
    print("\nResponse:")
    os.system(command)

def add_node_peer(node_id, enode_url, numNodes, first_rpc_port=8545):
    # For node #1
    # curl -X POST --data '{"jsonrpc":"2.0","method":"admin_addPeer","params":["<EnodeNode1>"],"id":1}' http://127.0.0.1:8546
    # curl -X POST --data '{"jsonrpc":"2.0","method":"admin_addPeer","params":["<EnodeNode1>"],"id":1}' http://127.0.0.1:8547
    # curl -X POST --data '{"jsonrpc":"2.0","method":"admin_addPeer","params":["<EnodeNode1>"],"id":1}' http://127.0.0.1:8548
    
    print(f"\n\nAdding node {node_id+1} as peer to all nodes with higher ID:")
    for i in range(node_id+1, numNodes):
        localhost_with_port = f"http://127.0.0.1:{first_rpc_port+i}"
        command = f'curl -X POST --data \'{{"jsonrpc":"2.0","method":"admin_addPeer","params":["{enode_url}"],"id":1}}\' {localhost_with_port}'
        print(f"\n - Adding node {node_id+1} as peer to node {i+1}:")
        print("  " + command)
        print(f"   Result:")
        os.system("  " + command)

def check_peer_nodes(numNodes, first_rpc_port=8545):
    # curl -X POST --data '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}' localhost:8545
    for i in range(numNodes):
        command = f'curl -X POST --data \'{{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}}\' localhost:{first_rpc_port+i}'
        print(f"\n\nChecking peer nodes for node {i+1}:")
        print(command)
        print(f"\nResult:")
        os.system(command)
    
def start_metrics(prometheus_configfile):
    # prometheus_status_command = "sudo systemctl status prometheus"
    # Command to finish grafana process = "sudo systemctl stop grafana server"
    start_metrics_command = f"cd prometheus && prometheus --config.file={prometheus_configfile}"
    start_grafana_command = "sudo systemctl start grafana-server"
    prometheus_metrics_http_service = "http://localhost:9090"
    
    # 0. End processes running on prometheus port 9090
    kill_process_on_port(9090)
    
    # 1. Start metrics in a console
    print("\n\nStarting metrics:")
    terminal_command = f"gnome-terminal --title='Metrics - Prometheus' -- bash -c '{start_metrics_command}; exec bash'"
    process = subprocess.Popen(terminal_command, shell=True)
    
    # 2. Open prometheus http service on default browser
    print(f"\n\nOpening Prometheus metrics service on default browser: {prometheus_metrics_http_service}")
    os.system(f"xdg-open {prometheus_metrics_http_service}")
    
    # 3. Start grafana
    print("\n\nStarting Grafana:")
    os.system(start_grafana_command)

def main():
    numNodes = 4
    first_rpc_port = 8545
    first_p2p_port = 30303
    first_metrics_port = 9545
    terminate_after = False
    prometheus_config = "prometheus.yml"
    
    setup_data(numNodes)

    # Start all nodes
    processes = []
    for i in range(numNodes):
        process = start_node(i, first_p2p_port, first_rpc_port, first_metrics_port)
        processes.append(process)

    # Ask input of enode url for each node
    enode_urls = []
    print("\n\n")
    for i in range(numNodes):
        enode_url = input(f"Enter enode URL for node {i+1}: ")
        enode_urls.append(enode_url)

    # Print enode URLs
    print("\n")
    for i, enode_url in enumerate(enode_urls):
        print(f"Node {i+1} enode URL: {enode_url}")
        
    # Add enode URLs for nodes to permissions configuration file
    for i in range(numNodes):
        add_enode_urls(enode_urls, first_rpc_port, i)
        
    # Add nodes as peers, we only do this for the first n-1 nodes, the last one does not need to be applied if we are using this command
    for i in range(numNodes-1):
        add_node_peer(i, enode_urls[i], numNodes, first_rpc_port)
        
    # Wait 2 seconds for the adding to occur
    time.sleep(2)
        
    check_peer_nodes(numNodes, first_rpc_port)
    
    # Start metrics
    start_metrics(prometheus_config)
    
    # Finish processes
    if terminate_after:
        # Stop nodes
        for process in processes:
            process.terminate()
            
    # Continuation for extra things
    # option = input("Enter an opcion ('exit' to finish Grafana): ")
    
if __name__ == "__main__":
    main()
    print("\n")
    
"""
Ports used: 8545, 8546, 8547, 8548, 30303, 30304, 30305, 30306, 9545, 9546, 9547, 9548, 9090
"""