import os
import requests
import configparser
from prettytable import PrettyTable
from colorama import init, Fore, Style

init(autoreset=True)

# Determine the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))

# Read configuration from config.ini in the script's directory
config_path = os.path.join(script_dir, 'configLorenz.ini')
# config_path = os.path.join(script_dir, 'configColgate.ini')
config = configparser.ConfigParser()
config.read(config_path)

# Salesforce credentials
instance_url = config.get('Salesforce', 'instance_url')
session_id = config.get('Salesforce', 'session_id')

# URL for the Tooling API endpoint
url = f"{instance_url}/services/data/v52.0/tooling/query/"

# Request headers
headers = {
    'Authorization': f'Bearer {session_id}',
    'Content-Type': 'application/json'
}

def retrieve_all_flows():
    query = "SELECT Id, DeveloperName, LatestVersionId, LatestVersion.VersionNumber FROM FlowDefinition"
    encoded_query = requests.utils.quote(query)
    full_url = f"{url}?q={encoded_query}"
    response = requests.get(full_url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get('records', [])

def retrieve_flow_definition_details(flow_api_name):
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

def get_user_selection(flow_versions):
    print(Fore.YELLOW + "Available Flow Versions:")
    table = PrettyTable()
    table.field_names = ["ID", "Version Number", "API Version", "Definition ID"]
    for fv in flow_versions:
        table.add_row([fv['Id'], fv['VersionNumber'], fv['ApiVersion'], fv['DefinitionId']])
    print(table)
    print(Fore.YELLOW + "Select the versions you want to delete (comma-separated, e.g., '1,3,5' or 'all' for all versions): ")
    user_input = input().strip().lower()
    if user_input == 'all':
        return [fv['Id'] for fv in flow_versions]
    else:
        selected_ids = [int(id.strip()) for id in user_input.split(',') if id.strip().isdigit()]
        return [fv['Id'] for fv in flow_versions if int(fv['VersionNumber']) in selected_ids]
    
def display_all_flows(all_flows):
    print(Fore.YELLOW + "\nAll Flows in the Org:")
    table = PrettyTable()
    table.field_names = ["Index", "ID", "Developer Name", "Latest Version ID", "Latest Version Number"]
    for index, flow in enumerate(all_flows, start=1):
        table.add_row([index, flow['Id'], flow['DeveloperName'], flow['LatestVersionId'], flow['LatestVersion']['VersionNumber']])
    print(table)

def get_user_selection_for_flows(all_flows):
    print(Fore.YELLOW + "Select the flows you want to process by entering the index numbers (comma-separated, e.g., '1,3,5'): ")
    user_input = input().strip()
    selected_indexes = [int(index.strip()) for index in user_input.split(',') if index.strip().isdigit()]
    return [all_flows[index - 1]['DeveloperName'] for index in selected_indexes if 1 <= index <= len(all_flows)]

def main():
    try:
        print(Fore.YELLOW + "Select an option:")
        print("1. Use flow(s) specified in the config.ini file")
        print("2. Query all flows in the org and make a selection")
        option = input("Enter your choice (1 or 2): ")

        if option == "1":
            flow_api_names = [flow_api_name.strip() for flow_api_name in config.get('Salesforce', 'flow_api_names').split(',')]
            for flow_api_name in flow_api_names:
                process_flow(flow_api_name)
        elif option == "2":
            all_flows = retrieve_all_flows()
            if all_flows:
                display_all_flows(all_flows)
                selected_flow_api_names = get_user_selection_for_flows(all_flows)
                if selected_flow_api_names:
                    config.set('Salesforce', 'flow_api_names', ','.join(selected_flow_api_names))
                    with open(config_path, 'w') as configfile:
                        config.write(configfile)
                    for flow_api_name in selected_flow_api_names:
                        process_flow(flow_api_name)
                else:
                    print(Fore.RED + "No flows selected.")
            else:
                print(Fore.RED + "No flows found in the org.")
        else:
            print(Fore.RED + "Invalid option selected.")
    except requests.exceptions.HTTPError as e:
        print(Fore.RED + f"HTTP Error: {e.response.status_code} {e.response.reason} {e.response.text}")
    except Exception as e:
        print(Fore.RED + f"General Error: {e}")

def process_flow(flow_api_name):
    flow_definition_info = retrieve_flow_definition_details(flow_api_name)
    if flow_definition_info:
        display_flow_definition_info(flow_definition_info)
        flow_versions = retrieve_flow_versions(flow_definition_info)
        if flow_versions:
            display_flow_versions(flow_versions)
            selected_ids = get_user_selection(flow_versions)
            if selected_ids:
                confirmation = input(Fore.YELLOW + "Are you sure you want to delete the selected Flow versions? (yes/no): ")
                if confirmation.lower() in ['yes', 'y']:
                    for flow_id in selected_ids:
                        delete_flow(flow_id)
                    print(Fore.GREEN + "Selected Flow versions deleted successfully!")
                else:
                    print(Fore.RED + "Deletion cancelled.")
            else:
                print(Fore.RED + "No Flow versions selected.")
        else:
            print(Fore.RED + "No Flow versions found.")
    else:
        print(Fore.RED + f"No FlowDefinition found for {flow_api_name}.")

if __name__ == "__main__":
    main()
