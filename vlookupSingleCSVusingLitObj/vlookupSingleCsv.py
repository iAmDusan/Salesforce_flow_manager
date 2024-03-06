# Used to lookup SFDC ids against External_Id__c
# Use the External ID when asking "what to look up against" after choosing object


import csv 
import sys 
import configparser 
import os
import time
from datetime import datetime 
from simple_salesforce import Salesforce 
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from termcolor import colored

# Class definition of CaseInsensitiveWordCompleter which inherits WordCompleter from prompt_toolkit
class CaseInsensitiveWordCompleter(WordCompleter):
    def __init__(self, words, ignore_case=True, **kwargs):
        if ignore_case:
            words = [word.lower() for word in words] # making the words case-insensitive
        super().__init__(words, **kwargs) # calling parent class constructor
        
    def get_completions(self, document, complete_event):
        # This method provides auto completions, it is called whenever the user types a character in the interface
        word_before_cursor = document.get_word_before_cursor(WORD=True) # Get the word before the cursor
        # get list of words that start with the word before cursor, ignoring the case
        completions = [word for word in self.words if word.lower().startswith(word_before_cursor.lower())]
        # yield completions by creating Completion objects, which will be displayed in the interface
        for completion in completions:
            yield Completion(completion, start_position=-len(word_before_cursor))

class CSVFileCompleter(Completer):
    def get_completions(self, document, complete_event):
        cwd = os.getcwd() # getting the current working directory using os module
        word_before_cursor = document.get_word_before_cursor(WORD=True) # get the word before the cursor
        csv_files = [f for f in os.listdir(cwd) if f.lower().endswith(".csv")] # get list of all csv files in current directory
        # filter csv files that start with the word before cursor, ignoring the case
        completions = [file for file in csv_files if file.lower().startswith(word_before_cursor.lower())]
        # return list of Completion objects, which will be used to provide auto completion in the interface
        return [
            Completion(file, start_position=-len(word_before_cursor), display=file)
            for file in completions
        ]
    
class ColumnNameCompleter(Completer):
    def __init__(self, csv_file):
        self.csv_file = csv_file

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        with open(self.csv_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            for header in headers:
                if header.lower().startswith(word_before_cursor.lower()):
                    yield Completion(header, start_position=-len(word_before_cursor))

def get_fields_for_object(sf, object_name):
    """
    Fetch the list of fields for the given Salesforce object.
    Use to Validate all csv column headers vs field names
    
    Args:
    - sf: The Salesforce connection instance.
    - object_name: The name of the Salesforce object.
    
    Returns:
    - A list of field names for the given Salesforce object.
    """
    try:
        # Use the describe method to get details about the object
        object_description = sf.__getattr__(object_name).describe()
        
        # Extract field names from the object description
        field_names = [field["name"] for field in object_description["fields"]]
        
        return field_names
    except Exception as e:
        print(f"Error fetching fields for object {object_name}: {e}")
        return []

# Constants for batch size and max retries
BATCH_SIZE = 5000  # Number of rows in each batch
MAX_RETRIES = 3  # Max number of retries for Salesforce query

def validate_csv_file(file_name, object_name, sf):
    errors = []
    csv.field_size_limit(2147483647)

    try:
        if object_name is None:
            raise ValueError("object_name cannot be None")

        object_fields = sf.__getattr__(object_name).describe()["fields"]
        field_names = [field["name"] for field in object_fields]  # Extract field names as a list
        field_summary = "\n".join([f"{field['name']}: {field['type']}" for field in object_fields])
        print(colored(f"Object fields for '{object_name}':\n{field_summary}", 'green'))

        query = f"SELECT {', '.join(field_names)} FROM {object_name}"
        print(colored(f"SOQL query: {query}", 'green'))

        with open(file_name, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader, [])
            for header in headers:
                if header not in field_names:
                    error_message = colored(f"CSV contains unknown field: {header}", 'red')
                    print(error_message)
                    errors.append(error_message)
    except Exception as e:
        error_message = colored(f"Error retrieving object fields for '{object_name}': {e}", 'red')
        print(error_message)
        errors.append(str(e))

    return errors

def vlookup_columns_in_csv(sf, csv_file, lookup_columns, default_ids, output_file=None):
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    output_file = output_file if output_file else csv_file.replace(".csv", "_with_SFDC_ids.csv")

    print(colored(f"Opening the CSV file {csv_file} for reading...", 'blue'))
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(colored(f"The CSV file contains {len(rows)} rows.", 'green'))

    renamed_fieldnames = []
    for col in rows[0].keys():
        if col in lookup_columns:
            renamed_fieldnames.append(col)
            renamed_fieldnames.append(f"_{col}")
        else:
            renamed_fieldnames.append(col)

    sf_ids = {col: {} for col in lookup_columns.keys()}

    print(colored("Gathering Salesforce IDs...", 'blue'))
    for col, obj_info in lookup_columns.items():
        obj_name = obj_info['object']
        lookup_field = obj_info['field']
        lookup_values = set(row[col] for row in rows if col in row)
        for chunk in chunks(list(lookup_values), 1000):
            ids_str = ",".join([f"'{str(id)}'" for id in chunk])

            for attempt in range(MAX_RETRIES):
                try:
                    query_string = f"SELECT Id, {lookup_field} FROM {obj_name} WHERE {lookup_field} IN ({ids_str})"
                    result = sf.query_all(query_string)
                    break
                except Exception as e:
                    print(colored(f"An error occurred while querying Salesforce: {e}", 'red'))
                    time.sleep(5)

            for record in result["records"]:
                if record[lookup_field] is not None:
                    sf_ids[col][record[lookup_field]] = record["Id"]

            if obj_name == 'User' and 'user' in default_ids:
                for val in chunk:
                    if val not in sf_ids[col]:
                        sf_ids[col][val] = default_ids['user']

    print(colored("All Salesforce IDs have been gathered. Now creating a new CSV file...", 'blue'))

    with open(output_file, "w", newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=renamed_fieldnames)
        writer.writeheader()
        for row in rows:
            new_row = {}
            for col in row.keys():
                if col in lookup_columns:
                    new_row[col] = sf_ids[col].get(row[col], "")
                    new_row[f"_{col}"] = row[col]
                else:
                    new_row[col] = row[col]
            writer.writerow(new_row)

    print(colored(f"Success! New CSV file '{output_file}' has been created with Salesforce IDs.", 'green'))


def menu(sf, commands, object_shortcuts, default_ids):
    choice = None

    while choice != "3":
        print("\n1. Validate CSV file against Salesforce object fields")
        print("2. vLookup column in CSV file")
        print("3. Exit")

        choice = prompt("\nEnter your choice: ", completer=WordCompleter(["1", "2", "3"]))

        if choice == "1":
            # Perform CSV validation
            shortcut = prompt(
                "\nEnter the Salesforce object name: ",
                completer=CaseInsensitiveWordCompleter(list(object_shortcuts.keys())),
            ).lower()  # Convert to lowercase to match the keys in object_shortcuts

            csv_file = prompt("Enter the csv file name: ", completer=CSVFileCompleter())

            # Here we convert the user input to lowercase to ensure it matches the keys in object_shortcuts
            validate_csv_file(csv_file, object_shortcuts.get(shortcut.lower()), sf)
        elif choice == "2":
            # Perform vLookup
            csv_file = prompt("Enter the csv file name: ", completer=CSVFileCompleter())
            if os.path.isfile(csv_file):
                lookup_columns = {}
                while True:
                    lookup_column = ""
                    while (
                        not lookup_column.strip()
                    ):  # keep asking until non-blank input is received
                        lookup_column = prompt(
                            "Enter a column name to lookup (or 'done' to finish): ",
                            completer=ColumnNameCompleter(csv_file),
                        )

                    if lookup_column.lower() == "done":
                        break

                    shortcut = prompt(
                        f"Enter the Salesforce object name for column '{lookup_column}': ",
                        completer=CaseInsensitiveWordCompleter(
                            list(object_shortcuts.keys())
                        ),
                    )
                    
                    # After getting the Salesforce object name from the user then get the field on that
                    actual_object_name = object_shortcuts.get(shortcut, "")
                    fields = get_fields_for_object(sf, actual_object_name)
                    field_completer = WordCompleter(fields, ignore_case=True)

                    lookup_field = prompt(
                        f"Enter the column on the {shortcut} to lookup against: ",
                        completer=field_completer
                    )

                    lookup_columns[lookup_column] = {
                        'object': object_shortcuts.get(shortcut, ""),
                        'field': lookup_field  # Storing the specific field for lookup
                    }

                if lookup_columns:
                    vlookup_columns_in_csv(sf, csv_file, lookup_columns, default_ids)

        elif choice == "3":
            print(colored("Exiting...", "green"))
            sys.exit(0)
        else:
            print(colored("Invalid choice. Please enter a number from the menu.", "red"))






def main():
    config = configparser.ConfigParser()

    try:
        config.read("config.ini")

        if "Salesforce" not in config:
            raise KeyError("Salesforce section is missing in the config.ini file")

        username = config["Salesforce"].get("username")
        password = config["Salesforce"].get("password")
        security_token = config["Salesforce"].get("security_token")

        if not username or not password or not security_token:
            raise ValueError("Salesforce credentials are missing in the config.ini file")
        
        object_shortcuts = {
            key.lower(): value for key, value in config["ObjectShortcuts"].items()
        }

        default_ids = {}
        if 'DefaultIDs' in config:
            default_ids = {
                key: value for key, value in config['DefaultIDs'].items()
            }

        sf = Salesforce(username=username, password=password, security_token=security_token)

        print(f"\nConnected to Salesforce instance: {sf.sf_instance}")

        org_query = "SELECT Id, Name FROM Organization LIMIT 1"
        org_info = sf.query(org_query)["records"][0]
        org_id = org_info["Id"]
        org_name = org_info["Name"]

        user_query = f"SELECT Id FROM User WHERE Username = '{username}'"
        user_info = sf.query(user_query)["records"][0]
        user_id = user_info["Id"]

        print("Connected to Salesforce org:")
        print("Org ID: " + org_id)
        print("Org Name: " + org_name)
        print("User ID: " + user_id)

        commands = [
            d["name"]
            for d in sf.describe()["sobjects"]
            if not any(
                sub in d["name"]
                for sub in ["__ChangeEvent", "__Feed", "__History", "__Share"]
            )
        ]

        while True:
            menu(sf, commands, object_shortcuts, default_ids)

    except FileNotFoundError:
        print("Configuration file 'config.ini' not found. If you are lost contact mdu@micronetbd.org")
    except KeyError as e:
        print(f"Invalid configuration file: {e}")
    except ValueError as e:
        print(f"Invalid configuration values: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
