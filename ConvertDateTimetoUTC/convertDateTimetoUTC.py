import argparse
import pandas as pd
import pytz
from datetime import datetime

'''
MUST SET INITIAL TIME ZONE. SCRIPT WILL CONVERT FROM THIS TimeZone to UTC
'''
def convert_to_utc(row, column_name):
    # central = pytz.timezone('US/Central')
    eastern = pytz.timezone('US/Eastern')
    utc = pytz.utc

    datetime_str = row[column_name]

    # Check for NaN or non-string values
    if pd.isna(datetime_str) or not isinstance(datetime_str, str):
        return "Invalid datetime format"

    # Try to match multiple formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f0000",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S"
    ]

    for fmt in formats:
        try:
            naive_datetime = datetime.strptime(datetime_str, fmt)
            aware_datetime = eastern.localize(naive_datetime)
            utc_datetime = aware_datetime.astimezone(utc)
            return utc_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        except ValueError:
            continue

    return "Invalid datetime format"


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Convert datetime columns from eastern Time to UTC in a CSV file.")
parser.add_argument("csv_file", type=str, help="Path to the input CSV file.")
args = parser.parse_args()

# Read the CSV file
df = pd.read_csv(args.csv_file)

while True:
    # Ask user for column name
    column_name = input("Enter the column name you want to convert to UTC (or 'done' to exit): ")
    
    if column_name.lower() == 'done':
        break
    
    # Check if the column exists
    if column_name not in df.columns:
        print(f"Column '{column_name}' not found.")
        continue
    
    # Create new column and apply the conversion
    new_column_name = f"{column_name}"
    df[new_column_name] = df.apply(lambda row: convert_to_utc(row, column_name), axis=1)
    
    # Rename original column and reorder the DataFrame
    df.rename(columns={column_name: f"_{column_name}"}, inplace=True)
    column_order = df.columns.tolist()
    column_order.remove(new_column_name)
    column_order.insert(column_order.index(f"_Original_TimeZone_{column_name}"), new_column_name)
    df = df[column_order]

# Save to new CSV
output_csv_file = f"utc_converted_{args.csv_file}"
df.to_csv(output_csv_file, index=False)
print(f"UTC converted CSV saved as {output_csv_file}.")
