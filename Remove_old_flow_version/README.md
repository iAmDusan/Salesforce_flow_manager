# Remove Old Flow Versions Script

## Overview

This Python script is designed to help Salesforce administrators remove old versions of flows from their Salesforce orgs. It utilizes the Salesforce Tooling API to retrieve information about flows and allows users to select which flows to delete.

## Requirements

- Python 3.x
- `requests` library (can be installed via `pip install requests`)
- A Salesforce org with API access and the necessary permissions to delete flows

## Configuration

1. Create a `config.ini` file in the same directory as the script.
2. Add your Salesforce instance URL and session ID to the `config.ini` file in the following format:

```
[Salesforce]
instance_url = YOUR_INSTANCE_URL
session_id = YOUR_SESSION_ID
```

Replace `YOUR_INSTANCE_URL` and `YOUR_SESSION_ID` with your Salesforce instance URL and session ID, respectively.

## Usage

1. Run the `removeAllFlowVersions.py` script.
2. The script will prompt you to confirm whether you want to delete the retrieved flows.
3. Type `yes` to confirm or `no` to cancel the deletion process.
4. The script will attempt to delete the selected flows. If any errors occur during the deletion process, it will display them.

## Notes

- Be cautious when using this script, as it will permanently delete flows from your Salesforce org.
- Make sure to review the list of flows before confirming the deletion to avoid accidental data loss.
