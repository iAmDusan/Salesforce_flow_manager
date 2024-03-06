import pyodbc
import configparser
import zlib
import csv
from io import BytesIO
from PIL import Image
import os
from tqdm import tqdm

# This script reads the DB information from the database.ini file.
# It then queries the Needles table "names_pictures", extracts the binary image data
# decompresses the data and outputs a png file in a directory whose name will be the names.names_id field

def extract_images(num_rows=None):
    # Read the database connection information from an INI file
    config = configparser.ConfigParser()
    config.read('database.ini')

    # Extract the connection parameters from the INI file
    server = config.get('database', 'server')
    database = config.get('database', 'database')
    trusted_connection = config.getboolean('database', 'trusted_connection')

    # Build the connection string
    connection_string = 'Driver={SQL Server Native Client 11.0};'
    connection_string += f'Server={server};Database={database};'
    if trusted_connection:
        connection_string += 'Trusted_Connection=yes;'
    else:
        username = config.get('database', 'username')
        password = config.get('database', 'password')
        connection_string += f'UID={username};PWD={password};'

    # Connect to the SQL Server database
    conn = pyodbc.connect(connection_string)

    # Retrieve the image data and associated account information from the database
    cursor = conn.cursor()
    if num_rows is None:
        cursor.execute('SELECT np.names_id, np.image_contents FROM names_picture np ORDER BY np.names_id ASC')
    else:
        cursor.execute(f'SELECT TOP {num_rows} np.names_id, np.image_contents FROM names_picture np ORDER BY np.names_id ASC')

    # Create a directory to store the images
    output_dir = input('Enter the output directory path (press Enter for the current directory): ')
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.getcwd()

   # os.makedirs(output_dir, exist_ok=True)

    # Create a progress bar to show the progress of the script
    progress_bar = tqdm(total=cursor.rowcount, desc='Extracting Images', unit='image')

    # Create an empty list to store the file paths of the extracted images
    manifest = []

    # Iterate over the rows and extract the images from the compressed binary data
    for row in cursor:
        # Extract the compressed binary image data from the row
        compressed_image_data = row[1]
        # Decompress the binary data
        image_data = zlib.decompress(compressed_image_data)
        # Convert the binary data to a bytes-like object
        image_bytes = BytesIO(image_data)
        # Open the image using PIL
        image = Image.open(image_bytes)
        # Build the output path for the image file
        output_path = os.path.join(str(row[0]), 'picture.png')
        # Create the directory for the account if it does not already exist
        os.makedirs(os.path.join(output_dir, str(row[0])), exist_ok=True)
        # Save the image to the output path
        image.save(os.path.join(output_dir, output_path), 'PNG')
        # Update the progress bar
        progress_bar.update(1)
        # Append the file path to the manifest list
        manifest.append((row[0], output_path))

    # Close the database connection
    conn.close()

    # Write the manifest file
    manifest_path = os.path.join(output_dir, 'manifest.csv')
    with open(manifest_path, 'w', newline='') as manifest_file:
        writer = csv.writer(manifest_file)
        writer.writerow(['Legacy Id', 'File Path'])
        for account_id, file_path in manifest:
            writer.writerow([account_id, file_path])

    print(f'{len(manifest)} images were extracted to {output_dir}.')
    print(f'The manifest was saved to {manifest_path}.')

if __name__ == '__main__':
    num_rows = input('Enter the number of rows to extract photos from (press Enter for all rows): ')
    if num_rows:
        num_rows = int(num_rows)

    extract_images(num_rows)