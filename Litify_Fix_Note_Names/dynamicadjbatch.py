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

# Define the date range and WHERE clause for finding "bad" records
start_date = datetime.date(2018, 1, 1)
end_date = datetime.date(2023, 6, 6)
bad_records_clause = f"CreatedDate < {end_date}T00:00:00Z AND Name LIKE 'a0x%'"

# Count "litify_pm__lit_Note__c" records with Salesforce ID as the Name
try:
    count_query = f"SELECT COUNT() FROM litify_pm__lit_Note__c WHERE {bad_records_clause}"
    record_count_result = sf.query(count_query)
    total_bad_records = record_count_result['totalSize']
    logging.info(f"Total 'litify_pm__lit_Note__c' records with Salesforce ID as the Name within the date range: {total_bad_records}")
except Exception as e:
    logging.error(f"An error occurred while counting 'litify_pm__lit_Note__c' records: {e}")

# User confirmation with total bad records count
proceed = input(f"This script will update records in Salesforce. There are {total_bad_records} 'litify_pm__lit_Note__c' records with Salesforce ID as the Name within the date range. Do you wish to proceed? (y/n): ")
if proceed.lower() != 'y':
    logging.info("Operation cancelled by user.")
    exit(0)

# Initialize variables
target_batch_size = 10000  # The desired batch size
delta = datetime.timedelta(days=7)
total_records_processed = 0

while start_date <= end_date:
    str_start_date = start_date.strftime('%Y-%m-%d')
    str_end_date = (start_date + delta).strftime('%Y-%m-%d')
    start_date += delta  # Decrease the start_date for the next run

    try:
        query = f"SELECT Id, Name, litify_pm__lit_Topic__c FROM litify_pm__lit_Note__c WHERE CreatedDate >= {str_start_date}T00:00:00Z AND CreatedDate < {str_end_date}T00:00:00Z"
        records = sf.query_all(query)
        records_to_process = records['records']

        if not records_to_process:
            logging.info(f"No records found for CreatedDate >= {str_start_date} AND CreatedDate < {str_end_date}.")
            continue

        # Filter records to update only those with 'a0x' in the Name
        updates_needed = [record for record in records_to_process if record['Name'].startswith('a0x')]

        if not updates_needed:
            logging.info(f"No records with 'a0x' in the Name found for CreatedDate >= {str_start_date} AND CreatedDate < {str_end_date}.")
            continue

        # Ensure each batch has as many records as possible up to the limit of 10,000
        while updates_needed:
            batch = updates_needed[:min(target_batch_size, len(updates_needed))]
            sf.bulk.litify_pm__lit_Note__c.update(batch)
            total_records_processed += len(batch)
            updates_needed = updates_needed[len(batch):]

            logging.info(f"{len(batch)} records updated successfully for CreatedDate >= {str_start_date} AND CreatedDate < {str_end_date}.")
            logging.info(f"Total records processed so far: {total_records_processed}")

    except SalesforceMalformedRequest as e:
        logging.error(f"Failed to update records: {e}")
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        exit(1)

logging.info("Script execution completed.")
