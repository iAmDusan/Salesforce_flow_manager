# This script takes the sql files located in the same folder as it and
# outputs them as csv files to a ne folder called CSV_OUTFILES

import os
import pyodbc
import pandas as pd
import warnings
import time
from tqdm import tqdm

# Suppress warnings at the UserWarning level
warnings.filterwarnings("ignore", category=UserWarning)

# Set the path for the .sql files
# "." For current directory
# ".." For one directory above
sql_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".")

# Connect to the database using Windows Authentication
connection = pyodbc.connect(
    "Driver={SQL Server};Server=localhost;Database=NeedlesKrasno;Trusted_Connection=yes;")

# Create the path for the csv output directory
csv_output_directory = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "CSV_OUTFILES")

# Create the csv output directory if it doesn't already exist
if not os.path.exists(csv_output_directory):
    os.makedirs(csv_output_directory)

# Use tqdm to display a progress bar for the total number of .sql files
for sql_file_path in tqdm(
    [
        os.path.join(dirpath, filename)
        for dirpath, dirnames, filenames in os.walk(sql_directory)
        for filename in filenames
        if filename.endswith(".sql")
    ],
    desc="SQL Files",
    unit="file",
):

    # Get the base name of the .sql file without the extension
    sql_file_base = os.path.splitext(os.path.basename(sql_file_path))[0]

    # Create the path for the corresponding csv file
    csv_directory = os.path.join(csv_output_directory, os.path.dirname(
        os.path.relpath(sql_file_path, sql_directory)))
    csv_file_path = os.path.join(csv_directory, f"{sql_file_base}.csv")

    # Create the csv directory if it doesn't already exist
    if not os.path.exists(csv_directory):
        os.makedirs(csv_directory)

    try:
        # Read the .sql file
        with open(sql_file_path, "r") as f:
            sql_query = f.read()

        # Execute the .sql file and store the result in a pandas DataFrame
        df = pd.read_sql_query(sql_query, connection)
        
        print(f"Processing {sql_file_base}...\nRows in query result: {len(df)}")

        # Write the result to a csv file
        df.to_csv(csv_file_path, index=False)
        
        print(f"{csv_file_path} complete\n")

    except Exception as e:
        with open("script_error.log", "a") as log_file:
            log_file.write(f"{sql_file_base}:{str(e)}\n")

# Close the database connection
connection.close()
print("Process complete.")
