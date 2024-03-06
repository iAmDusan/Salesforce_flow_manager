from simple_salesforce import Salesforce
import csv
import sys
import configparser
import readline
import os
from datetime import datetime

# Functions for field value validation
def validate_value(value, field_type):
    if field_type == 'string':
        return True
    elif field_type == 'boolean':
        return value.lower() in ['true', 'false']
    elif field_type == 'int':
        try:
            int(value)
            return True
        except ValueError:
            return False
    elif field_type == 'double':
        try:
            float(value)
            return True
        except ValueError:
            return False
    elif field_type == 'date':
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    else:
        # Add validation for other field types here
        return True

# Function to validate CSV file against Salesforce object fields
def validate_csv_file(file_name, object_fields):
    errors = []
    # increase the field size limit
    csv.field_size_limit(2147483647) # max value for a 32-bit integer for long text fields
    with open(file_name, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        # Validate fields once using CSV headers
        for header in headers:
            if header not in object_fields:
                error_message = f"CSV contains unknown field: {header}"
                print(error_message)
                errors.append(error_message)
        row_number = 1 # Starts from 1 considering the header row. For identifying error rows
        for row in reader:
            row_number += 1 # Increment the row number for each row
            for field_name, value in row.items():
                if field_name not in object_fields:
                    continue
                field_type = object_fields[field_name]['type']
                if not validate_value(value, field_type):
                    error_message = f"Invalid value for field '{field_name}' with type '{field_type}' at row {row_number}: {value}"
                    print(error_message)
                    errors.append(error_message)
    return errors

# Define the list completer
# This is for auto-completing inputs
def list_completer(text, state):
    line = readline.get_line_buffer()
    if not line:
        return [c + " " for c in commands][state]
    else:
        line_lower = line.lower()
        completions = [c + " " for c in commands if c.lower().startswith(line_lower)]
        return completions[state].strip()  # Remove the trailing space after autocompletion


# Fetch credentials
config = configparser.ConfigParser()
config.read('credentials.ini')

sf_credentials = {}
if 'Salesforce' in config:
    sf_credentials = config['Salesforce']
else:
    sf_credentials['username'] = input('Enter Salesforce username: ')
    sf_credentials['password'] = input('Enter Salesforce password: ')
    sf_credentials['security_token'] = input('Enter Salesforce security token: ')
    config['Salesforce'] = sf_credentials
    with open('credentials.ini', 'w') as configfile:
        config.write(configfile)

# Connect to Salesforce
sf = Salesforce(username=sf_credentials['username'], password=sf_credentials['password'], security_token=sf_credentials['security_token'])

# Fetch object metadata
commands = [obj['name'] for obj in sf.describe()["sobjects"]]

# Retrieve org information
# Output org information to the user
# Retrieve org information
org_query = "SELECT Id, Name FROM Organization LIMIT 1"
org_info = sf.query(org_query)["records"][0]
org_id = org_info["Id"]
org_name = org_info["Name"]

# Retrieve user information
user_query = f"SELECT Id FROM User WHERE Username = '{sf_credentials['username']}'"
user_info = sf.query(user_query)["records"][0]
user_id = user_info["Id"]

# Output org information to the user
print("Connected to Salesforce org:")
print("Org ID: " + org_id)
print("Org Name: " + org_name)
print("User ID: " + user_id)


# get auto-compelte ready and get user input
readline.set_completer(list_completer)
readline.parse_and_bind("tab: complete")
obj_name = input("Enter the Salesforce object name: ")
object_fields = {field['name']: field for field in sf.__getattr__(obj_name).describe()['fields']}

# Fetch CSV file name
commands = os.listdir()
csv_file = input("Enter the csv file name: ")

errors = validate_csv_file(csv_file, object_fields)

# Write errors to a file
with open('errors.txt', 'w') as f:
    for error in errors:
        f.write(f"{error}\n")
