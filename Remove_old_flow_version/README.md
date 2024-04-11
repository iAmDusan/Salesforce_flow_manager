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
Replace YOUR_SALESFORCE_INSTANCE_URL with your Salesforce org's instance URL, YOUR_SALESFORCE_SESSION_ID with your valid Salesforce session ID, and FLOW_API_NAME_1, FLOW_API_NAME_2, etc., with the API names of the flows you want to manage (comma-separated)
```

## Script Overview

The script performs the following tasks:

- Imports necessary libraries: `os`, `requests`, `configparser`, `PrettyTable`, and `colorama`.
- Reads configuration from a `config.ini` file.
- Determines the directory where the script is located.
- Initializes colorama for colored output.
- Points out the area where the `config.ini` file is declared.

## Code Snippet

```python
import os
import requests
import configparser
from prettytable import PrettyTable
from colorama import init, Fore, Style

init(autoreset=True)

# Determine the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))

# Read configuration from config.ini in the script's directory
config_path = os.path.join(script_dir, 'config.ini')
Config File Declaration
The area where the config.ini file is declared is as follows:

python
Copy code
config_path = os.path.join(script_dir, 'config.ini')
In the snippet above, the config.ini file path is constructed using the os.path.join() function, combining the script_dir (directory where the script is located) with the filename config.ini.
