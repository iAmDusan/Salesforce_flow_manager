import configparser
from simple_salesforce import Salesforce
from tabulate import tabulate

# Read Salesforce connection parameters and query file name from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Salesforce connection parameters
sid = config['Salesforce']['sid']
instance = config['Salesforce']['instance']

# Connect to Salesforce
sf = Salesforce(session_id=sid, instance=instance)

# Read SOQL query from file
with open(config['Salesforce']['query_file'], 'r') as file:
    soql_query = file.read()

# Execute the query
query_result = sf.query_all(soql_query)['records']

# Prepare data for tabulate
table_data = []
for record in query_result:
    truncated_description = record['Description'][:40] if record['Description'] else ''
    table_data.append([
        record['Id'],
        record['WhatId'],
        record['Subject'],
        record['CreatedBy']['Name'],
        truncated_description,
        record['CreatedDate']
    ])

# Define headers
headers = ["Id", "WhatId", "Subject", "Created By", "Description", "Matter"]

# Print tabulated data
print(tabulate(table_data, headers=headers, tablefmt="grid"))
