import os
import requests
import configparser
from prettytable import PrettyTable
from colorama import init, Fore, Style

init(autoreset=True)

# Determine the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))

# Read configuration from config.ini in the script's directory
config_path = os.path.join(script_dir, 'configLorenzSandbox.ini')
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
    query = "SELECT Id, DeveloperName, LatestVersionId, LatestVersion.VersionNumber, LatestVersion.Status FROM FlowDefinition"
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
    
    if response.status_code == 400 and "DELETE_FAILED" in response.text:
        print(Fore.YELLOW + f"Skipping deletion of active flow version with ID '{flow_id}'.")
    else:
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
    table.field_names = ["Index", "ID", "Developer Name", "Latest Version ID", "Latest Version Number", "Active"]
    for index, flow in enumerate(all_flows, start=1):
        is_active = flow['LatestVersion']['Status'] == 'Active'
        table.add_row([index, flow['Id'], flow['DeveloperName'], flow['LatestVersionId'], flow['LatestVersion']['VersionNumber'], "Yes" if is_active else "No"])
    print(table)

def get_user_selection_for_flows(all_flows):
    print(Fore.YELLOW + "Select the flows you want to process by entering the index numbers (comma-separated, e.g., '1,3,5'): ")
    user_input = input().strip()
    selected_indexes = [int(index.strip()) for index in user_input.split(',') if index.strip().isdigit()]
    return [all_flows[index - 1]['DeveloperName'] for index in selected_indexes if 1 <= index <= len(all_flows)]

def display_active_flows(all_flows):
    print(Fore.YELLOW + "\nActive Flows in the Org:")
    table = PrettyTable()
    table.field_names = ["Index", "ID", "Developer Name", "Active Version ID", "Active Version Number"]
    for index, flow in enumerate(all_flows, start=1):
        table.add_row([index, flow['Id'], flow['DeveloperName'], flow['LatestVersionId'], flow['LatestVersion']['VersionNumber']])
    print(table)

def delete_inactive_versions(flow_definition_info):
    flow_versions = retrieve_flow_versions(flow_definition_info)
    active_version_id = flow_definition_info['LatestVersionId']
    inactive_versions = [fv for fv in flow_versions if fv['Id'] != active_version_id]
    
    if inactive_versions:
        print(Fore.YELLOW + f"Deleting inactive versions for flow: {flow_definition_info['DeveloperName']}")
        for fv in inactive_versions:
            delete_flow(fv['Id'])
        print(Fore.GREEN + f"Inactive versions deleted successfully for flow: {flow_definition_info['DeveloperName']}")
    else:
        print(Fore.YELLOW + f"No inactive versions found for flow: {flow_definition_info['DeveloperName']}")

def get_org_info():
    query_url = f"{instance_url}/services/data/v52.0/query?q=SELECT+Id,+Name,+IsSandbox,+OrganizationType+FROM+Organization"
    response = requests.get(query_url, headers=headers)
    response.raise_for_status()
    data = response.json()
    org_info = data['records'][0]
    return org_info

def display_org_info(org_info):
    print(Fore.YELLOW + "Org Information:")
    table = PrettyTable()
    table.field_names = ["Instance Name", "Org ID", "Is Sandbox", "Organization Type"]
    is_sandbox = org_info.get('IsSandbox', False) or 'sandbox' in instance_url.lower()
    org_type = org_info.get('OrganizationType', 'Unknown')
    org_id = org_info.get('Id', 'Unknown')
    table.add_row([org_info['Name'], org_id, "Yes" if is_sandbox else "No", org_type])
    print(table)
    if not is_sandbox:
        print(Fore.RED + "WARNING: This is likely a PRODUCTION org!")

def main():
    try:
        org_info = get_org_info()
        if org_info:
            display_org_info(org_info)
        else:
            print(Fore.RED + "Unable to retrieve org information.")

        while True:
            print(Fore.YELLOW + "\nSelect an option:")
            print("1. Use flow(s) specified in the config.ini file")
            print("2. Query all flows in the org and make a selection")
            print("3. Display active flows and delete their inactive versions")
            print("4. Exit")
            option = input("Enter your choice (1, 2, 3, or 4): ")

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
            elif option == "3":
                all_flows = retrieve_all_flows()
                if all_flows:
                    display_active_flows(all_flows)
                    confirmation = input(Fore.YELLOW + "Do you want to delete all inactive versions for the listed active flows? (yes/no): ")
                    if confirmation.lower() in ['yes', 'y']:
                        for flow in all_flows:
                            delete_inactive_versions(flow)
                    else:
                        print(Fore.RED + "Deletion cancelled.")
                else:
                    print(Fore.RED + "No active flows found in the org.")
            elif option == "4":
                print(Fore.GREEN + "Exiting the script.")
                break
            else:
                print(Fore.RED + "Invalid option selected. Please try again.")
    except requests.exceptions.HTTPError as e:
        print(Fore.RED + f"HTTP Error: {e.response.status_code} {e.response.reason} {e.response.text}")
    except Exception as e:
        print(Fore.RED + f"General Error: {e}")





def delete_all_versions_except_active(flow_definition_info):
    flow_versions = retrieve_flow_versions(flow_definition_info)
    active_version_id = flow_definition_info['LatestVersionId']
    inactive_versions = [fv for fv in flow_versions if fv['Id'] != active_version_id]
    
    if inactive_versions:
        print(Fore.YELLOW + f"Deleting inactive versions for flow: {flow_definition_info['DeveloperName']}")
        for fv in inactive_versions:
            delete_flow(fv['Id'])
        print(Fore.GREEN + f"Inactive versions deleted successfully for flow: {flow_definition_info['DeveloperName']}")
    else:
        print(Fore.YELLOW + f"No inactive versions found for flow: {flow_definition_info['DeveloperName']}")


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
