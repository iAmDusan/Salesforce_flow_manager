import csv
import os

# Define the maximum number of rows per file
MAX_ROWS_PER_FILE = 1000000

# Define the name of the input file
INPUT_FILE = 'input.csv'

# Define the directory where the output files will be saved
OUTPUT_DIR = 'output'

# Make sure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Open the input file for reading
with open(INPUT_FILE, 'r') as input_file:

    # Read the input file as a CSV
    reader = csv.reader(input_file)

    # Get the headers from the input file
    headers = next(reader)

    # Initialize a counter to keep track of the number of rows
    row_count = 0

    # Initialize a counter to keep track of the number of output files
    file_count = 1

    # Initialize a variable to hold the current output file
    output_file = None

    # Loop through the rows in the input file
    for row in reader:

        # If this is the first row of a new output file
        if row_count % MAX_ROWS_PER_FILE == 0:

            # If there's already an output file open, close it
            if output_file is not None:
                output_file.close()

            # Open a new output file
            output_filename = f'{OUTPUT_DIR}/{os.path.splitext(INPUT_FILE)[0]}_{file_count}.csv'
            output_file = open(output_filename, 'w', newline='')
            writer = csv.writer(output_file)

            # Write the headers to the new output file
            writer.writerow(headers)

            # Increment the file count
            file_count += 1

        # Write the row to the current output file
        writer.writerow(row)

        # Increment the row count
        row_count += 1

        # Display progress updates every 100,000 rows
        if row_count % 100000 == 0:
            print(f'Processed {row_count} rows...')

    # If there's an output file open, close it
    if output_file is not None:
        output_file.close()

# Display a message when the script is finished
print(f'Finished processing {row_count} rows into {file_count - 1} output files.')
