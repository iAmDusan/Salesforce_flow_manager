import os
import configparser
import pyodbc
import pandas as pd
import time
import warnings
from tabulate import tabulate
from colorama import Fore, Style, init


def log_error(message):
    with open('error_log.txt', 'a') as log_file:
        log_file.write(message + "\n")

def print_execution_summary(total_queries, total_time, errors):
    # convert total_time into minute:seoconds
    # divmod = divide and modulo
    # Return the tuple (x//y, x%y). Invariant: div*y + mod == x.
    minutes, seconds = divmod(total_time, 60)
    
    total_time_str = f"{int(minutes)} minutes, {int(seconds)} seconds"
    print(Style.BRIGHT + "\n" + "-" * 60)
    print(Fore.YELLOW + "Execution Summary:" + Style.RESET_ALL)
    print(tabulate([
        ["Total Queries Run", total_queries],
        ["Total Execution Time", f"{total_time_str} "],
        ["Errors", len(errors)]
    ], headers=["Metric", "Value"]))
    if errors:
        print(Fore.RED + "\nErrors:" + Style.RESET_ALL)
        for error in errors:
            print(error)
    print("-" * 60)

# Suppress user warnings to keep console clean
warnings.simplefilter(action='ignore', category=UserWarning)

# region Read the config.ini file
config = configparser.ConfigParser()
config.read('config.ini')
local_server = config['database']['local_server']
remote_server = config['database']['remote_server']
database = config['database']['database']
username = config['database']['username']
password = config['database']['password']
# endregion

# Try to connect using Windows Authentication
try:
    print("Trying to connect using Windows Authentication...")
    conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={local_server};Database={database};Trusted_Connection=yes;"
    conn = pyodbc.connect(conn_str)
    print("Connected using Windows Authentication.")
except pyodbc.Error:
    print("Windows Authentication failed. Trying SQL Server Authentication...")
    conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={remote_server};Database={database};UID={username};PWD={password};"
    conn = pyodbc.connect(conn_str)
    print("Connected using SQL Server Authentication.")


# Initialize variables for summary
total_queries = 0
total_time = 0
errors = []

# Set SQL an CSV Folder names Create CSV folder if it does not exist already
sql_folder = 'SQL'
csv_folder = 'CSV'
os.makedirs(csv_folder, exist_ok=True)

# Traverse the SQL folder and eventually exec each
for root, dirs, files in os.walk(sql_folder):
    dirs[:] = [d for d in dirs if not d.startswith('_')]

    for file in files:
        if file.endswith('.sql'):
            file_path = os.path.join(root, file)
            # Compute the relative path from the SQL folder
            relative_path = os.path.relpath(root, sql_folder)

            with open(file_path, 'r') as sql_file:
                sql_query = sql_file.read()

                print(Style.BRIGHT + Fore.BLUE + f"\nRunning query from file: {file_path}" + Style.RESET_ALL)
                total_queries += 1

                try:
                    start_time = time.time()

                    df = pd.read_sql(sql_query, conn)

                    elapsed_time = time.time() - start_time
                    total_time += elapsed_time
                    print(f"Execution Time: {Fore.GREEN}{elapsed_time:.2f} seconds{Style.RESET_ALL} | Rows: {Fore.LIGHTYELLOW_EX}{len(df)}{Style.RESET_ALL}")

                    # Create corresponding directories in the CSV folder
                    output_dir = os.path.join(csv_folder, relative_path)
                    os.makedirs(output_dir, exist_ok=True)

                    output_csv = os.path.join(output_dir, f"{os.path.splitext(file)[0]}.csv")
                    df.to_csv(output_csv, index=False, mode='w', encoding='utf-8', sep=',')
                    print(Fore.CYAN + f"Output saved to: {output_csv}" + Style.RESET_ALL)

                except Exception as e:
                    error_message = f"Error processing file: {file_path} - {str(e)}"
                    print(Fore.RED + error_message + Style.RESET_ALL)
                    log_error(error_message)
                    errors.append(error_message)

conn.close()

# Print summary of execution time and total queries run
print_execution_summary(total_queries, total_time, errors)