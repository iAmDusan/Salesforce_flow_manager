import configparser  # https://docs.python.org/3/library/configparser.html
import csv  # https://docs.python.org/3/library/csv.html
import os  # https://docs.python.org/3/library/os.html
import shutil  # https://docs.python.org/3/library/shutil.html
import sys  # https://docs.python.org/3/library/sys.html
import pandas as pd  # https://pandas.pydata.org/docs/
from simple_salesforce import Salesforce  # https://simple-salesforce.readthedocs.io/en/latest/
from termcolor import colored  # https://pypi.org/project/termcolor/
from prompt_toolkit import prompt  # https://python-prompt-toolkit.readthedocs.io/en/latest/
from prompt_toolkit.completion import WordCompleter  # https://python-prompt-toolkit.readthedocs.io/en/latest/pages/asking_for_input.html#completion

## To add
## verify all col
## add 'new' column name for found col instead of {col_name}._SFDCID


def get_all_csv_headers():
    csv_headers = {}

    # Walk through the current directory and its subdirectories
    for root, dirs, files in os.walk('.'):
        for file in files:
            # If the file is a CSV
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    for header in headers:
                        csv_headers[header.lower()] = file_path

    return csv_headers

def fetch_sfdc_ids(sf, object_name, lookup_field, values):
    """
    Query Salesforce for record IDs where the lookup field matches the values from the CSV.
    Returns a dictionary with the lookup values as keys and the matching Salesforce IDs as values.
    """
    # Convert values to strings and filter out blank values
    non_blank_values = [str(value) for value in values if str(value).strip()]

    # Query Salesforce for the IDs
    query = f"SELECT Id, {lookup_field} FROM {object_name} WHERE {lookup_field} != NULL"
    result = sf.query_all(query)
    records = result.get('records', [])

    # Map the lookup values to the Salesforce IDs
    id_dict = {str(record[lookup_field]): record['Id'] for record in records}

    return id_dict


def process_csv_file(sf, csv_file, lookup_dict, output_dir, file_count, file_index):
    try:
        df = pd.read_csv(csv_file, dtype=str)
        base_filename = os.path.basename(csv_file)
        new_filename = base_filename[:-4] + "_output.csv"
        os.makedirs(output_dir, exist_ok=True)
        processed_file = os.path.join(output_dir, new_filename)
        processed_df = df.copy()
        lookup_dict_lower = {column.lower(): (sfdc_object, lookup_field) for column, (sfdc_object, lookup_field) in lookup_dict.items()}

        for column, (sfdc_object, lookup_field) in lookup_dict_lower.items():
            matched_columns = [col for col in df.columns if col.lower() == column]
            if matched_columns:
                new_column_name = f"{column}_SFDCID"
                lookup_column_index = df.columns.get_loc(matched_columns[0])
                processed_df.insert(lookup_column_index, new_column_name, None)

                unique_values = df[matched_columns[0]].unique()

                try:
                    sfdc_ids = fetch_sfdc_ids(sf, sfdc_object, lookup_field, unique_values)
                except Exception as e:
                    print(f"Failed to fetch Salesforce IDs due to: {e}")
                    return

                for index, row in df.iterrows():
                    lookup_value = row[matched_columns[0]]
                    sfdc_id = sfdc_ids.get(lookup_value)
                    if sfdc_id is not None:
                        processed_df.at[index, new_column_name] = sfdc_id
        processed_df.to_csv(processed_file, index=False)
        
        # Update progress
        progress = int((file_index + 1) / file_count * 100)
        sys.stdout.write('\r')
        sys.stdout.write(f"Processed file {file_index + 1} of {file_count} - {progress}% complete")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"An error occurred while processing the file {csv_file}: {e}")


def lookup_all_csv(sf, object_shortcuts):
    try:
        csv_headers = get_all_csv_headers()
        lookup_dict = {}

        while True:
            column_name = prompt("Enter a column name (or 'done' to finish):\n",
                                 completer=WordCompleter(csv_headers, ignore_case=True))
            if column_name.lower() == 'done':
                break
            elif column_name.lower() not in csv_headers:
                print(colored("Invalid column name. Please try again.", "red"))
                continue

            while True:
                sfdc_object_shortcut = prompt("Enter a Salesforce object (or 'done' to finish):\n",
                                               completer=WordCompleter(list(object_shortcuts.keys()), ignore_case=True))
                if sfdc_object_shortcut.lower() == 'done':
                    break
                sfdc_object = object_shortcuts.get(sfdc_object_shortcut.lower())
                if not sfdc_object:
                    print(colored(f"Invalid Salesforce object: {sfdc_object_shortcut}", "red"))
                    continue

                # Describe the Salesforce object to get its fields
                try:
                    sobject_desc = getattr(sf, sfdc_object).describe()
                    sobject_fields = [field['name'] for field in sobject_desc['fields'] if field['externalId']]
                    print(f"Available External ID fields: {sobject_fields}")
                except Exception as e:
                    print(colored(f"Error while describing Salesforce object: {e}", "red"))
                    continue

                while True:
                    sfdc_field = prompt("Enter a Salesforce external ID field (or 'done' to finish):\n",
                                         completer=WordCompleter(sobject_fields, ignore_case=True))
                    if sfdc_field.lower() == 'done':
                        break
                    elif sfdc_field not in sobject_fields:
                        print(colored(f"Invalid field: {sfdc_field}", "red"))
                        continue
                    else:
                        lookup_dict[column_name] = (sfdc_object, sfdc_field)
                        break  # This will exit the field selection loop

                break  # This will exit the object selection loop

        # Get the output directory path
        output_dir = os.path.join(os.getcwd(), 'vlookOut')
        csv_files_to_process = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.csv'):
                    with open(os.path.join(root, file), 'r') as f:
                        headers = [header.lower() for header in csv.reader(f).__next__()]
                        if set(headers).intersection(set(lookup_dict.keys())):
                            csv_files_to_process.append(os.path.join(root, file))
        if csv_files_to_process:
            print("The following CSV files will be processed:")
            for csv_file in csv_files_to_process:
                print(csv_file)
            proceed = input("\nPlease make sure all the above files are closed before proceeding. Do you want to proceed? (yes/no): ")
            if proceed.lower() == 'yes':
                file_count = len(csv_files_to_process)
                for i, csv_file in enumerate(csv_files_to_process):
                    try:
                        print(f"\nProcessing file: {csv_file}")
                        process_csv_file(sf, csv_file, lookup_dict, output_dir, file_count, i)
                    except Exception as e:
                        print(f"Failed to process file {csv_file} due to: {e}")
            else:
                print("Operation cancelled.")
        else:
            print("\nNo CSV files found for the entered column names. Please try again.")
    except Exception as e:
        print(f"An error occurred during lookup: {e}")


def menu(sf, commands, object_shortcuts):
    # Set objects
    print("\nPlease select an option:")
    print(colored("1. Lookup all CSV", "cyan"))
    print(colored("2. Exit", "cyan"))

    option = input()

    if option == '1':
        lookup_all_csv(sf, object_shortcuts)
    elif option == '2':
        print("Exiting program...")
        exit(0)
    else:
        print(colored("Invalid option. Please try again.", "red"))


def main():
    config = configparser.ConfigParser()

    try:
        config.read("config.ini")

        if "Salesforce" not in config:
            raise KeyError("Salesforce section is missing in the config.ini file")

        username = config["Salesforce"].get("username")
        password = config["Salesforce"].get("password")
        security_token = config["Salesforce"].get("security_token")

        # Load Salesforce object shortcuts from the config file
        object_shortcuts = config["ObjectShortcuts"]

        if not username or not password or not security_token:
            raise ValueError("Salesforce credentials are missing in the config.ini file")

        sf = Salesforce(username=username, password=password, security_token=security_token)

        # Create the 'vlookOut' directory if it doesn't exist
        output_dir = os.path.join(os.getcwd(), 'vlookOut')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)  # Delete the existing directory
        os.makedirs(output_dir)

        # Print the Salesforce instance URL and user details
        print(colored(f"\nConnected to Salesforce instance: {sf.sf_instance}", "green"))

        # Retrieve org information
        org_query = "SELECT Id, Name FROM Organization LIMIT 1"
        org_info = sf.query(org_query)["records"][0]
        org_id = org_info["Id"]
        org_name = org_info["Name"]

        # Retrieve user information
        user_query = f"SELECT Id FROM User WHERE Username = '{username}'"
        user_info = sf.query(user_query)["records"][0]
        user_id = user_info["Id"]

        # Output org information to the user
        print("Connected to Salesforce org:")
        print("Org ID: " + org_id)
        print("Org Name: " + org_name)
        print("User ID: " + user_id)

        # Load the commands (Salesforce object names)
        commands = [
            obj["name"]
            for obj in sf.describe()["sobjects"]
            if not any(
                sub in obj["name"]
                for sub in ["__ChangeEvent", "__Feed", "__History", "__Share"]
            )
        ]

        while True:
            menu(sf, commands, object_shortcuts)

    except FileNotFoundError:
        print(
            colored(
                "Configuration file 'config.ini' not found. If you are lost contact mdu@micronetbd.org",
                "red",
            )
        )
    except KeyError as e:
        print(colored(f"Invalid configuration file: {e}", "red"))
    except ValueError as e:
        print(colored(f"Invalid configuration values: {e}", "red"))
    except Exception as e:
        print(colored(f"An error occurred: {e}", "red"))


if __name__ == "__main__":
    main()
