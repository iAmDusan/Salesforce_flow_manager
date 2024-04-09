import requests
import configparser
from prettytable import PrettyTable
from colorama import Fore, Style

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Salesforce credentials
instance_url = config.get('Salesforce', 'instance_url')
session_id = config.get('Salesforce', 'session_id')
flow_api_name = config.get('Salesforce', 'flow_api_name')

# URL for the Tooling API endpoint
url = f"{instance_url}/services/data/v52.0/tooling/query/"

# Request headers
headers = {
    'Authorization': f'Bearer {session_id}',
    'Content-Type': 'application/json'
}

def retrieve_flow_details():
    try:
        # Construct the SOQL query to retrieve extended Flow details
        query = f"""
        SELECT Id, MasterLabel, VersionNumber, CreatedDate, FlowType, Metadata FROM Flow 
        WHERE MasterLabel = '{flow_api_name}'
        """
        # Sending the request to query the Flow details
        response = requests.get(url, headers=headers, params={'q': query})
        response.raise_for_status()

        # Parse the response JSON
        data = response.json()
        flows_info = []

        # Check if the query returned any records
        if 'records' in data:
            flow_records = data['records']
            for flow_record in flow_records:
                flow_info = {
                    'Id': flow_record['Id'],
                    'MasterLabel': flow_record['MasterLabel'],
                    'VersionNumber': flow_record['VersionNumber'],
                    'CreatedDate': flow_record['CreatedDate'],
                    'FlowType': flow_record['FlowType'],
                    'URL': f"{instance_url}/{flow_record['Id']}"
                }
                flows_info.append(flow_info)
        else:
            print(f"No Flow records found with Master Label '{flow_api_name}'.")

        return flows_info
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving Flow details: {e}")
        return []

def print_flows_table(flows_info):
    table = PrettyTable()
    table.field_names = ["ID", "Label", "Version", "Created Date", "Type", "URL"]
    for flow in flows_info:
        table.add_row([
            Fore.CYAN + flow['Id'] + Style.RESET_ALL,
            flow['MasterLabel'],
            flow['VersionNumber'],
            flow['CreatedDate'],
            flow['FlowType'],
            Fore.GREEN + flow['URL'] + Style.RESET_ALL
        ])
    print(table)

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

# Main execution block
try:
    # Retrieve Flow details
    flows_info = retrieve_flow_details()

    # Print the retrieved Flow details
    if flows_info:
        print_flows_table(flows_info)

        # Ask for confirmation before deletion
        confirmation = input("Are you sure you want to delete the above Flow(s)? (yes/no): ")
        if confirmation.lower() == 'yes':
            for flow_info in flows_info:
                delete_flow(flow_info)
        else:
            print("Deletion cancelled.")
    else:
        print(f"No Flow found with Master Label '{flow_api_name}'.")
except Exception as e:
    print(f"Error: {e}")
