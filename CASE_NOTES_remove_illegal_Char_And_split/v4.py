import csv
import os
import time
import re
from rich.console import Console
from rich.progress import Progress

MAX_ROWS_PER_FILE = 250000
INPUT_FILE = 'Case_Notes.csv'
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
csv.field_size_limit(10 * 1024 * 1024)
console = Console()

# Define the regular expressions outside of the function for efficiency
allowed_chars_re = re.compile(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]')
specific_illegal_chars_re = re.compile(r'[\x0F\x0E\x05\x9D\x1A\x02\x03]')

def clean_cell(cell_content):
    """Clean the cell content by removing specific illegal characters and handling quotation marks.
    Keeps allowed characters"""

    # Remove characters outside the allowable XML 1.0 character range
    cleaned_content = allowed_chars_re.sub('', cell_content)

    # Remove specific illegal characters
    cleaned_content = specific_illegal_chars_re.sub('', cleaned_content)

    # Replace double quotation mark with single quotation mark
    cleaned_content = cleaned_content.replace('"', '\'')
    
    return cleaned_content



row_count = 0
file_count = 1

# Begin progress bar for nice output
progress = Progress(console=console)
start_time = time.time()

with progress:
    task = progress.add_task("[cyan]Processing...", total=MAX_ROWS_PER_FILE)

    with open(INPUT_FILE, 'r', encoding='utf-8') as input_file:
        reader = csv.DictReader(input_file)
        headers = reader.fieldnames

        for row in reader:
            if row_count % MAX_ROWS_PER_FILE == 0:
                if row_count > 0:
                    writer.writeheader()
                    writer.writerows(rows_buffer)
                    output_file.close()
                    progress.log(f"[cyan]{output_filename} saved successfully. Rows written: {len(rows_buffer)}")

                output_filename = f'{OUTPUT_DIR}/{os.path.splitext(INPUT_FILE)[0]}_{file_count}.csv'
                output_file = open(output_filename, 'w', newline='', encoding='utf-8')
                writer = csv.DictWriter(output_file, fieldnames=headers)
                file_count += 1
                rows_buffer = []
                task = progress.add_task(f"[cyan]Processing {output_filename}...", total=MAX_ROWS_PER_FILE)

            cleaned_row = {key: clean_cell(value) for key, value in row.items()}
            rows_buffer.append(cleaned_row)
            row_count += 1
            progress.update(task, advance=1)

            if row_count % 50000 == 0:
                elapsed_time = time.time() - start_time
                progress.update(task, description=f"[cyan]Processing {output_filename}... Elapsed time: {elapsed_time:.2f} seconds, Rows processed: {row_count}")

        if rows_buffer:
            writer.writeheader()
            writer.writerows(rows_buffer)
            output_file.close()
            progress.log(f"[cyan]{output_filename} saved successfully. Rows written: {len(rows_buffer)}")

console.log(f"[green]Process completed. Total rows processed: {row_count}")
