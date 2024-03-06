import os
import pandas as pd
from simple_salesforce import Salesforce
import readline

# establish Salesforce connection
sf = Salesforce(username='litify@micronetbd.org.demo4', password='certify-slashed-yearning-jersey-simile-dispose1@', security_token='F60dzJtFdXU9WhhMNlPmzGKC7')

# ask user for Salesforce object API name then get desc
api_name = input("Enter the API name of the Salesforce object to validate: ")
description = getattr(sf, api_name).describe()

# extract field names from the object description
sf_fields = {field['name'].lower() for field in description['fields']}

# Register the completer function
# This is solely so you can tab-complete the filename you are using below
def completer(text, state):
    options = [i for i in os.listdir() if i.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

# ask user for CSV file name
csv_file = input("Enter the name of the CSV file to validate: ")

# read the CSV file as a pandas DataFrame
df = pd.read_csv(csv_file, low_memory=False)

# extract column names from the DataFrame
csv_columns = set(df.columns.str.lower())

# get the base name of the CSV file (without extension) to use in the output file name
base_csv_filename = os.path.splitext(csv_file)[0]

# specify a unique output file name for each CSV file
output_file = f'{base_csv_filename}_results.txt'

# compare Salesforce fields with CSV columns
with open(output_file, 'w') as file:
    if csv_columns.issubset(sf_fields):
        file.write(f'All headers in {csv_file} match Salesforce fields.\n')
    else:
        mismatched_fields = csv_columns - sf_fields
        file.write(f'Warning: The following headers in {csv_file} do not match Salesforce fields: {mismatched_fields}\n')

