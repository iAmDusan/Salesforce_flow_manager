# Salesforce Flow Version Management Script

This Python script allows you to manage Flow versions in a Salesforce org. It provides two options for selecting the flows to process:

1. Use the flow(s) specified in the `config.ini` file.
2. Query all flows in the org and make a selection.

## Prerequisites

Before running the script, ensure that you have the following:

- Python 3.x installed
- Required Python packages: `requests`, `configparser`, `prettytable`, `colorama`
- Salesforce org credentials (instance URL and session ID)

## Configuration

1. Create a `config.ini` file in the same directory as the script.
2. Add the following sections and parameters to the `config.ini` file:

```ini
[Salesforce]
instance_url = YOUR_SALESFORCE_INSTANCE_URL
session_id = YOUR_SALESFORCE_SESSION_ID
flow_api_names = FLOW_API_NAME_1, FLOW_API_NAME_2
Replace YOUR_SALESFORCE_INSTANCE_URL with your Salesforce org's instance URL, YOUR_SALESFORCE_SESSION_ID with your valid Salesforce session ID, and FLOW_API_NAME_1, FLOW_API_NAME_2, etc., with the API names of the flows you want to manage (comma-separated).