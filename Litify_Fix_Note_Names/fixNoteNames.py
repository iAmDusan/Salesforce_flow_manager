from simple_salesforce import Salesforce, SalesforceMalformedRequest
import logging
import configparser
import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Read credentials from config.ini
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    username = config['Salesforce']['username']
    password = config['Salesforce']['password']
    security_token = config['Salesforce']['security_token']
except KeyError as e:
    logging.error(f"Missing key in config.ini: {e}")
    exit(1)
except Exception as e:
    logging.error(f"Failed to read config.ini: {e}")
    exit(1)

# Connect to Salesforce
try:
    sf = Salesforce(username=username, password=password, security_token=security_token)
    logging.info("Successfully connected to Salesforce.")
except Exception as e:
    logging.error(f"Failed to connect to Salesforce: {e}")
    exit(1)

# User interaction
proceed = input("This script will update records in Salesforce. Do you wish to proceed? (y/n): ")
if proceed.lower() != 'y':
    logging.info("Operation cancelled by user.")
    exit(0)

# Initialize variables
batch_size = 10000  # Increase this number based on your API limits
start_date = datetime.date(2022, 1, 1)  # Modify start date as needed
end_date = datetime.date(2023, 6, 6)  # Modify end date as needed
delta = datetime.timedelta(days=7)  # Increase or decrease this based on the desired chunk size

while start_date <= end_date:
    str_start_date = start_date.strftime('%Y-%m-%d')
    str_end_date = (start_date + delta).strftime('%Y-%m-%d')
    start_date += delta  # Prepare for the next iteration

    try:
        # Fetch records
        query = f"SELECT Id, litify_pm__lit_Topic__c FROM litify_pm__lit_Note__c WHERE CreatedDate >= {str_start_date}T00:00:00Z AND CreatedDate < {str_end_date}T00:00:00Z LIMIT {batch_size}"
        records = sf.query_all(query)

        if not records['records']:
            logging.info(f"No records found for CreatedDate >= {str_start_date} AND CreatedDate < {str_end_date}.")
            continue

        # Update records
        for record in records['records']:
            record['Name'] = record['litify_pm__lit_Topic__c']

        # Use Bulk API to update
        sf.bulk.litify_pm__lit_Note__c.update(records['records'])
        
        logging.info(f"{len(records['records'])} records updated successfully for CreatedDate >= {str_start_date} AND CreatedDate < {str_end_date}.")

    except SalesforceMalformedRequest as e:
        logging.error(f"Failed to update records: {e}")
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        exit(1)
