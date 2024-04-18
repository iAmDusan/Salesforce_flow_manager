# salesforce_api.py
import requests

class SalesforceAPI:
    def __init__(self, instance_url, headers):
        self.instance_url = instance_url
        self.headers = headers

    def retrieve_all_flows(self):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = "SELECT Id, DeveloperName, LatestVersionId, ActiveVersionId, ActiveVersion.VersionNumber, LatestVersion.VersionNumber, LastModifiedDate FROM FlowDefinition"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('records', [])

    def retrieve_flow_definition_details(self, flow_api_name):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = f"SELECT Id, DeveloperName, LatestVersionId, ActiveVersionId, ActiveVersion.VersionNumber, LatestVersion.VersionNumber FROM FlowDefinition WHERE DeveloperName = '{flow_api_name}'"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        if data['records']:
            return data['records'][0]
        else:
            return None

    def retrieve_flow_versions(self, flow_definition_info):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = f"SELECT Id, ApiVersion, VersionNumber, DefinitionId FROM Flow WHERE DefinitionId = '{flow_definition_info['Id']}' ORDER BY VersionNumber ASC"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('records', [])

    def delete_flow(self, flow_id):
        delete_flow_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/Flow/{flow_id}"
        response = requests.delete(delete_flow_url, headers=self.headers)
        if response.status_code == 400 and "DELETE_FAILED" in response.text:
            raise Exception(f"Skipping deletion of active flow version with ID '{flow_id}'.")
        else:
            response.raise_for_status()

    def delete_flowdefinition(self, flow_definition_id):
        delete_flowdefinition_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/FlowDefinition/{flow_definition_id}"
        response = requests.delete(delete_flowdefinition_url, headers=self.headers)
        response.raise_for_status()

    def get_org_info(self):
        query_url = f"{self.instance_url}/services/data/v52.0/query?q=SELECT+Id,+Name,+IsSandbox,+OrganizationType+FROM+Organization"
        response = requests.get(query_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        org_info = data['records'][0]
        return org_info