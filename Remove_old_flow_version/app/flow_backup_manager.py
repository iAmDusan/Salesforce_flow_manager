import os
import requests
import json
import logging
import xmltodict
from datetime import datetime
import xml.etree.ElementTree as ET

# Configure logging
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
                flow_info = retrieve_flow_definition_details(flow_api_name)
                if flow_info:
                    self.backup_flow(flow_info, backup_dir, text_area, retrieve_flow_versions, flow_api_name)
                else:
                    logging.warning(f"Flow definition not found for {flow_api_name}. Skipping backup.")
                    text_area.append(f"Flow definition not found for {flow_api_name}. Skipping backup.\n")
            else:
                logging.warning(f"Flow item not found for ID {flow_id}. Skipping backup.")
                text_area.append(f"Flow item not found for ID {flow_id}. Skipping backup.\n")

        text_area.append("Backup completed.\n")

    def backup_flow(self, flow_info, backup_dir, text_area, retrieve_flow_versions, flow_api_name):
        flow_versions = retrieve_flow_versions(flow_info)
        if not flow_versions:
            text_area.append(f"No versions found for {flow_api_name}. Skipping backup.\n")
            return

        # Create directories for FlowDefinitions and Flows
        flow_def_dir = os.path.join(backup_dir, "force-app", "main", "default", "flowDefinitions")
        flow_dir = os.path.join(backup_dir, "force-app", "main", "default", "flows")
        os.makedirs(flow_def_dir, exist_ok=True)
        os.makedirs(flow_dir, exist_ok=True)

        # Save the FlowDefinition metadata
        flow_def_path = os.path.join(flow_def_dir, f"{flow_api_name}.flowDefinition-meta.xml")
        flow_metadata_path = os.path.join(flow_dir, f"{flow_api_name}.flow-meta.xml")
        
        # Generate and save FlowDefinition XML
        flow_def_xml = self.generate_xml({
            'activeVersionNumber': str(max([v['VersionNumber'] for v in flow_versions]))
        }, "FlowDefinition")
        with open(flow_def_path, "w") as file:
            file.write(flow_def_xml)

        for version in flow_versions:
            version_metadata = self.retrieve_flow_version_metadata(version['Id'])
            if version_metadata:
                version_path = os.path.join(flow_dir, f"{flow_api_name}-{version['VersionNumber']}.flow")
                
                # Save prettified JSON
                prettified_json = json.dumps(version_metadata, indent=4)
                with open(version_path + ".json", "w") as json_file:
                    json_file.write(prettified_json)
                
                # Convert JSON to XML and save
                try:
                    xml_data = xmltodict.unparse({'Flow': version_metadata}, pretty=True)
                    modified_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_data}'
                    with open(version_path, "w") as xml_file:
                        xml_file.write(modified_xml)
                except Exception as e:
                    logging.error(f"Error converting JSON to XML: {e}")
                    text_area.append(f"Error converting JSON to XML for version {version['VersionNumber']}. Skipping backup.\n")
            else:
                text_area.append(f"Failed to retrieve metadata for version {version['VersionNumber']}. Skipping backup.\n")



    def restore_flow_definition(self, backup_file_path):
        flow_file = os.path.basename(backup_file_path)
        flow_api_name = flow_file[:-9]  # Remove the ".flow.json" extension
        flow_path = backup_file_path[:-5]  # Remove the ".json" extension

        backup_dir = os.path.dirname(os.path.dirname(flow_path))
        flow_def_dir = os.path.join(backup_dir, "force-app", "main", "default", "flowDefinitions")
        flow_def_path = os.path.join(flow_def_dir, f"{flow_api_name}.flowDefinition-meta.xml")

        # Load and parse the FlowDefinition XML
        with open(flow_def_path, "r") as file:
            flow_def_xml = file.read()
        flow_def_data = xmltodict.parse(flow_def_xml)["FlowDefinition"]

        # Create the FlowDefinition
        create_flow_def_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/FlowDefinition/"
        create_flow_def_data = {
            "DeveloperName": flow_api_name,
            "ActiveVersionNumber": flow_def_data["activeVersionNumber"],
            "Description": flow_def_data.get("description", "")
        }
        response = requests.post(create_flow_def_url, headers=self.headers, json=create_flow_def_data)
        response.raise_for_status()
        flow_definition_id = response.json()["id"]

        # Restore Flow
        self.restore_flow_version(flow_definition_id, flow_path)
    
    def restore_flow(self, flow_api_name, flow_path):
        flow_dir = os.path.dirname(flow_path)
        flow_def_path = os.path.join(flow_dir, f"{flow_api_name}.flowDefinition-meta.xml")

        # Load and parse the FlowDefinition XML
        with open(flow_def_path, "r") as file:
            flow_def_xml = file.read()
        flow_def_data = xmltodict.parse(flow_def_xml)["FlowDefinition"]

        # Create the FlowDefinition
        create_flow_def_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/FlowDefinition/"
        create_flow_def_data = {
            "DeveloperName": flow_api_name,
            "ActiveVersionNumber": flow_def_data["activeVersionNumber"],
            "Description": flow_def_data.get("description", "")
        }
        response = requests.post(create_flow_def_url, headers=self.headers, json=create_flow_def_data)
        response.raise_for_status()
        flow_definition_id = response.json()["id"]

        # Restore Flow
        self.restore_flow_version(flow_definition_id, flow_path)

    def restore_flow_version(self, flow_definition_id, flow_path):
        flow_path_json = flow_path + ".json"

        # Load and parse the Flow JSON
        with open(flow_path_json, "r") as file:
            flow_json = json.load(file)

        # Create the Flow
        create_flow_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/Flow/"
        create_flow_data = {
            "DefinitionId": flow_definition_id,
            "VersionNumber": flow_json["versionNumber"],
            "ApiVersion": flow_json["apiVersion"],
            "Status": "Active" if flow_json["versionNumber"] == int(flow_json["activeVersionNumber"]) else "Inactive",
            "Description": flow_json.get("description", ""),
            "ProcessType": flow_json["processType"],
            "Flow": flow_json["flow"]
        }
        response = requests.post(create_flow_url, headers=self.headers, json=create_flow_data)
        response.raise_for_status()
        logging.info(f"Flow version {flow_json['versionNumber']} for '{flow_json['developerName']}' restored successfully.")




    def convert_xml_to_json(self, xml_element):
        json_data = {}
        for child in xml_element:
            if len(child) == 0:
                json_data[child.tag] = child.text
            else:
                json_data[child.tag] = self.convert_xml_to_json(child)
        return json_data

    def generate_xml(self, metadata, object_type):
        xml_parts = [f'<?xml version="1.0" encoding="UTF-8"?>\n<{object_type} xmlns="http://soap.sforce.com/2006/04/metadata">']
        for key, value in metadata.items():
            xml_parts.append(f'    <{key}>{value}</{key}>')
        xml_parts.append(f'</{object_type}>')
        return '\n'.join(xml_parts)

    def generate_flow_xml(self, flow_info):
        # This should generate the complete XML for a Flow based on `flow_info`
        # Placeholder: return a full XML string as per Salesforce Metadata API requirements
        return "<Flow>...</Flow>"

    def retrieve_flow_version_metadata(self, version_id):
        retrieve_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/Flow/{version_id}"
        response = requests.get(retrieve_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()  # Ensure this JSON is correctly formatted as expected by xmltodict
        else:
            logging.error(f"Failed to retrieve metadata for version ID {version_id}: HTTP {response.status_code}")
            return None