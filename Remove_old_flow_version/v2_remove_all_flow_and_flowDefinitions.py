import requests
import configparser
from prettytable import PrettyTable
from colorama import init, Fore, Style

init(autoreset=True)

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('./remove_old_flow_version/config.ini')

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

def retrieve_flow_definition_details():
    query = f"SELECT Id, DeveloperName, LatestVersionId, LatestVersion.VersionNumber FROM FlowDefinition WHERE DeveloperName = '{flow_api_name}'"
    encoded_query = requests.utils.quote(query)
    full_url = f"{url}?q={encoded_query}"
    response = requests.get(full_url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data['records'][0] if data.get('records') else None

def retrieve_flow_versions(flow_definition_info):
    query = f"SELECT Id, ApiVersion, VersionNumber, DefinitionId FROM Flow WHERE DefinitionId = '{flow_definition_info['Id']}' ORDER BY VersionNumber ASC"
    encoded_query = requests.utils.quote(query)
    full_url = f"{url}?q={encoded_query}"
    response = requests.get(full_url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get('records', [])

def delete_flow(flow_id):
    delete_flow_url = f"{instance_url}/services/data/v52.0/tooling/sobjects/Flow/{flow_id}"
    response = requests.delete(delete_flow_url, headers=headers)
    response.raise_for_status()
    print(Fore.GREEN + f"Flow with ID '{flow_id}' deleted successfully.")

def display_flow_definition_info(flow_definition_info):
    print(Fore.YELLOW + "FlowDefinition Details:")
    table = PrettyTable()
    table.field_names = ["ID", "Developer Name", "Latest Version ID", "Latest Version Number"]
    table.add_row([flow_definition_info['Id'], flow_definition_info['DeveloperName'], flow_definition_info['LatestVersionId'], flow_definition_info['LatestVersion']['VersionNumber']])
    print(table)

def display_flow_versions(flow_versions):
    print(Fore.YELLOW + "\nFlow Versions:")
    table = PrettyTable()
    table.field_names = ["ID", "Version Number", "API Version", "Definition ID"]
    for fv in flow_versions:
        table.add_row([fv['Id'], fv['VersionNumber'], fv['ApiVersion'], fv['DefinitionId']])
    print(table)

def main():
    try:
        flow_definition_info = retrieve_flow_definition_details()
        if flow_definition_info:
            display_flow_definition_info(flow_definition_info)
            flow_versions = retrieve_flow_versions(flow_definition_info)
            if flow_versions:
                display_flow_versions(flow_versions)
                confirmation = input(Fore.YELLOW + "Are you sure you want to delete all the Flow versions? (yes/no): ")
                if confirmation.lower() == 'yes':
                    for flow_version in flow_versions:
                        delete_flow(flow_version['Id'])
                    print(Fore.GREEN + "All Flow versions deleted successfully!")
                else:
                    print(Fore.RED + "Deletion cancelled.")
            else:
                print(Fore.RED + "No Flow versions found.")
        else:
            print(Fore.RED + "No FlowDefinition found.")
    except requests.exceptions.HTTPError as e:
        print(Fore.RED + f"HTTP Error: {e.response.status_code} {e.response.reason} {e.response.text}")
    except Exception as e:
        print(Fore.RED + f"General Error: {e}")

if __name__ == "__main__":
    main()
