import os
import requests
import logging
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class FlowBackupManager:
    def __init__(self, instance_url, headers):
        self.instance_url = instance_url
        self.headers = headers

    def backup_flows(self, selected_flows, backup_dir, text_area, find_flow_item_by_id, retrieve_flow_definition_details, retrieve_flow_versions):
        if not os.path.exists(backup_dir):
            logging.error(f"Backup directory does not exist: {backup_dir}")
            text_area.append(f"Error: Backup directory does not exist: {backup_dir}\n")
            return

        for flow_id in selected_flows:
            flow_item = find_flow_item_by_id(flow_id)
            if flow_item:
                flow_api_name = flow_item.text(1)
                logging.debug(f"Processing backup for: {flow_api_name}")
                flow_info = retrieve_flow_definition_details(flow_api_name)
                if flow_info:
                    self.backup_flow(flow_info, backup_dir, text_area, retrieve_flow_versions)
                else:
                    logging.warning(f"Flow definition not found for {flow_api_name}. Skipping backup.")
                    text_area.append(f"Flow definition not found for {flow_api_name}. Skipping backup.\n")
            else:
                logging.warning(f"Flow item not found for ID {flow_id}. Skipping backup.")
                text_area.append(f"Flow item not found for ID {flow_id}. Skipping backup.\n")

        text_area.append("Backup completed.\n")

    def retrieve_flow_version_metadata(self, version_id):
        retrieve_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/Flow/{version_id}"
        response = requests.get(retrieve_url, headers=self.headers)
        if response.status_code == 200:
            try:
                # Parse JSON and extract needed data
                data = response.json()  # Convert JSON response to dictionary
                return data['Metadata']  # Assuming 'Metadata' is the correct key; adjust if necessary
            except KeyError as e:
                logging.error(f"KeyError: {str(e)} - Check the JSON response structure.")
                return None
        else:
            logging.error(f"API Request Failed: Status Code {response.status_code}")
            return None

    def backup_flow(self, flow_info, backup_dir, text_area, retrieve_flow_versions):
        flow_api_name = flow_info['DeveloperName']
        flow_versions = retrieve_flow_versions(flow_info)
        if not flow_versions:
            text_area.append(f"No versions found for {flow_api_name}. Skipping backup.\n")
            return

        flow_backup_dir = os.path.join(backup_dir, "force-app", "main", "default", "flows")
        os.makedirs(flow_backup_dir, exist_ok=True)

        metadata_path = os.path.join(flow_backup_dir, f"{flow_api_name}.flow-meta.xml")
        with open(metadata_path, "w") as file:
            file.write(self.generate_xml(flow_info, "FlowDefinition"))

        for version in flow_versions:
            version_metadata = self.retrieve_flow_version_metadata(version['Id'])
            if version_metadata:
                version_path = os.path.join(flow_backup_dir, f"{flow_api_name}-{version['VersionNumber']}.flow")
                try:
                    with open(version_path, "w") as file:
                        file.write(json.dumps(version_metadata))  # Convert dictionary to JSON string before writing
                except Exception as e:
                    text_area.append(f"Failed to write version {version['VersionNumber']} for {flow_api_name} to {version_path}: {e}\n")
            else:
                text_area.append(f"Failed to retrieve metadata for version {version['VersionNumber']}. Skipping backup.\n")



    def generate_xml(self, metadata, object_type):
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<{object_type} xmlns="http://soap.sforce.com/2006/04/metadata">\n'
        for key, value in metadata.items():
            xml += f'    <{key}>{value}</{key}>\n'
        xml += f'</{object_type}>'
        return xml