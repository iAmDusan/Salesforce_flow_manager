import os
import configparser
import pyodbc
import pandas as pd
from pathlib import Path
import warnings

def log_error(message):
    with open('error_log.txt', 'a') as log_file:
        log_file.write(message + "\n")

# supress user warnings to keep console clean
warnings.simplefilter(action='ignore', category=UserWarning)

# Read the config.ini file
config = configparser.ConfigParser()
config.read('config.ini')
local_server = config['database']['local_server']
remote_server = config['database']['remote_server']
database = config['database']['database']
username = config['database']['username']
password = config['database']['password']

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

# Create a CSV folder if it doesn't exist
csv_folder = 'CSV'
os.makedirs(csv_folder, exist_ok=True)

# Find and execute SQL files
sql_folder = 'SQL'
for root, _, files in os.walk(sql_folder):
   
    for file in files:
        if file.endswith('.sql'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as sql_file:
                sql_query = sql_file.read()
                print(f"Running query from file: {file_path}")

                try:
                    # Execute the query and save the result as a CSV
                    df = pd.read_sql(sql_query, conn)

                    # Determine the output folder for the CSV file
                    relative_path = os.path.relpath(root, sql_folder)
                    output_folder = os.path.join(csv_folder, relative_path)
                    os.makedirs(output_folder, exist_ok=True)

                    # Save the output CSV maintaining the same directory structure
                    output_csv = os.path.join(output_folder, f"{os.path.splitext(file)[0]}.csv")
                    df.to_csv(output_csv, index=False, mode='w', encoding='utf-8', sep=',')
                    print(f"Saved output to: {output_csv}")

                except Exception as e:
                    error_message = f"Error while processing file: {file_path}\nError: {str(e)}"
                    print(error_message)
                    log_error(error_message)

# Close the connection
conn.close()
print("Done.")
