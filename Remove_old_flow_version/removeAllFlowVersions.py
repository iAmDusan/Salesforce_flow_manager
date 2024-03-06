import requests
import configparser

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Salesforce credentials
instance_url = config.get('Salesforce', 'instance_url')
session_id = config.get('Salesforce', 'session_id')

# URL for the Tooling API endpoint
url = f"{instance_url}/services/data/v52.0/tooling/query/"

# Flow Master Label to delete
flow_master_label = 'Auto Populate Intake'  # Change this to the desired flow Master Label

# Request headers
headers = {
    'Authorization': f'Bearer {session_id}',
    'Content-Type': 'application/json'
}

def retrieve_flow_details():
    try:
        flows_info = []

        # Construct the SOQL query to retrieve Flow details
        query = f"SELECT Id, MasterLabel FROM Flow WHERE MasterLabel = '{flow_master_label}'"

        # Sending the request to query the Flow details
        response = requests.get(url, headers=headers, params={'q': query})
        response.raise_for_status()

        # Parse the response JSON
        data = response.json()

        # Check if the query returned any records
        if 'records' in data:
            flow_records = data['records']
            for flow_record in flow_records:
                flow_info = {
                    'Id': flow_record['Id'],
                    'MasterLabel': flow_record['MasterLabel']
                }
                flows_info.append(flow_info)
        else:
            print(f"No Flow records found with Master Label '{flow_master_label}'.")

        return flows_info
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving Flow details: {e}")
        return []

def delete_flow(flow_info):
    try:
        flow_id = flow_info['Id']
        flow_label = flow_info['MasterLabel']

        # Construct the URL for deleting the Flow
        delete_url = f"{instance_url}/services/data/v52.0/tooling/sobjects/Flow/{flow_id}"

        # Sending the request to delete the Flow
        response = requests.delete(delete_url, headers=headers)
        response.raise_for_status()

        print(f"Flow '{flow_label}' with ID '{flow_id}' deleted successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error deleting Flow '{flow_label}' with ID '{flow_id}': {e}")

try:
    # Retrieve Flow details
    flows_info = retrieve_flow_details()

    # Print the retrieved Flow details
    if flows_info:
        total_flows = len(flows_info)
        print(f"Retrieved {total_flows} Flow(s) with Master Label '{flow_master_label}':")
        for flow_info in flows_info:
            print(f"ID: {flow_info['Id']}, Label: {flow_info['MasterLabel']}")
        
        # Ask for confirmation before deletion
        confirmation = input("Are you sure you want to delete the above Flow(s)? (yes/no): ")
        if confirmation.lower() == 'yes':
            for flow_info in flows_info:
                delete_flow(flow_info)
        else:
            print("Deletion cancelled.")
    else:
        print(f"No Flow found with Master Label '{flow_master_label}'.")
except Exception as e:
    print(f"Error: {e}")
