# Flow Management Tool

The Flow Management Tool is a desktop application developed using PyQt5. It facilitates the management of Salesforce Flow Definitions by enabling users to query, backup, and delete flow versions through a user-friendly graphical interface. This tool is particularly useful for Salesforce administrators and developers looking to streamline their workflow management processes.

## Features

- **Query Flow Definitions**: Retrieve all flows from a Salesforce instance with options to filter by active or inactive statuses.
- **Backup Flows**: Selectively backup flow definitions to a local directory.
- **Delete Flow Versions**: Delete specific flow versions, keeping only the active or the latest ones.
- **Interactive UI**: A GUI that provides easy navigation and operation of flow management tasks.

## Installation

### Prerequisites

- Python 3.6 or later.
- PyQt5
- Requests
- `prettytable` for tabular data presentation.
- Access to a Salesforce instance with API access enabled.

### Setup

Install Dependencies:

Bash
pip install -r requirements.txt
Use code with caution.
Create Configuration File (INI):

Create an INI file (e.g., config.ini) in your project directory.
Add the following structure:
Ini, TOML
[Salesforce]
instance_url = <https://your_instance.salesforce.com>
sid = your_salesforce_session_id  
Use code with caution.
Replace placeholders with your Salesforce instance URL and session ID.

## Usage

Run the application (e.g., python flow_manager.py)
The graphical interface will guide you through managing your Salesforce Flows.
Notes:

Instructions for obtaining your Salesforce session ID can be found within Salesforce documentation.
Ensure proper security measures for storing your sensitive Salesforce credentials.
