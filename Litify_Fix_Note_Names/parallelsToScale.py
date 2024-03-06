from simple_salesforce import Salesforce, SalesforceMalformedRequest
import logging
import configparser

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

# Initial count query to get the total number of bad records
bad_records_clause = "Name LIKE 'a0x%'"
count_query = f"SELECT COUNT() FROM litify_pm__lit_Note__c WHERE {bad_records_clause}"
record_count_result = sf.query(count_query)
total_bad_records = record_count_result['totalSize']

# User Confirmation
proceed = input(f"There are {total_bad_records} bad records. Do you wish to proceed? (y/n): ")
if proceed.lower() != 'y':
    logging.info("Operation cancelled by user.")
    exit(0)

# Initialize variables
target_batch_size = 10000
total_records_processed = 0
last_id = ''  # Keep track of the last processed Id

while total_records_processed < total_bad_records:
    try:
        if last_id:
            query = f"SELECT Id, Name, litify_pm__lit_Topic__c FROM litify_pm__lit_Note__c WHERE {bad_records_clause} AND Id > '{last_id}' ORDER BY Id ASC LIMIT {target_batch_size}"
        else:
            query = f"SELECT Id, Name, litify_pm__lit_Topic__c FROM litify_pm__lit_Note__c WHERE {bad_records_clause} ORDER BY Id ASC LIMIT {target_batch_size}"
            
        records = sf.query_all(query)
        records_to_process = records['records']
        
        if not records_to_process:
            logging.info(f"No more records to process.")
            break

        # Batch update
        sf.bulk.litify_pm__lit_Note__c.update(records_to_process)
        
        num_processed = len(records_to_process)
        total_records_processed += num_processed

        # Update last_id for the next batch
        last_id = records_to_process[-1]['Id']
        
        logging.info(f"{num_processed} records updated successfully.")
        logging.info(f"Total records processed so far: {total_records_processed}")
        
    except SalesforceMalformedRequest as e:
        logging.error(f"Failed to update records: {e}")
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        exit(1)

logging.info("Script execution completed.")
