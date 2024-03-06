import csv
import os
import time
from rich.console import Console
from rich.progress import Progress

MAX_ROWS_PER_FILE = 500000
MAX_CELL_SIZE = 1048576  # Excel's maximum cell size
INPUT_FILE = 'Case_Notes.csv'
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
csv.field_size_limit(10 * 1024 * 1024)
console = Console()

def split_large_cell(cell_content):
    """Split the content of a large cell into a list of chunks."""
    return [cell_content[i:i+MAX_CELL_SIZE] for i in range(0, len(cell_content), MAX_CELL_SIZE)]

large_col_name = "litify_pm__lit_Note__c"
large_col_index = None  # This will be determined later
max_splits = 0

with open(INPUT_FILE, 'r', encoding='utf-8') as input_file:
    reader = csv.DictReader(input_file)
    headers = reader.fieldnames
    large_col_index = headers.index(large_col_name)

    row_count = 0
    file_count = 1
    output_file = None
    file_row_counts = {}
    files_with_splits = set()

    progress = Progress(console=console)

    max_cell_length = 0
    start_time = time.time()

    with progress:
        task = progress.add_task("[cyan]Processing...", total=MAX_ROWS_PER_FILE)

        for row in reader:
            if row_count % MAX_ROWS_PER_FILE == 0:
                if output_file is not None:
                    progress.log(f"[cyan]Saving {output_filename}...")
                    writer = csv.DictWriter(output_file, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(rows_buffer)
                    output_file.close()
                    progress.log(f"[cyan]{output_filename} saved successfully.")

                output_filename = f'{OUTPUT_DIR}/{os.path.splitext(INPUT_FILE)[0]}_{file_count}.csv'
                output_file = open(output_filename, 'w', newline='', encoding='utf-8')
                file_count += 1
                file_row_counts[output_filename] = 0
                rows_buffer = []
                task = progress.add_task(f"[cyan]Processing {output_filename}...", total=MAX_ROWS_PER_FILE)

            if len(row[large_col_name]) > MAX_CELL_SIZE:
                chunks = split_large_cell(row[large_col_name])
                for i in range(len(chunks)):
                    if i > max_splits:
                        max_splits = i
                    if i == 0:
                        row[large_col_name] = chunks[i]
                    else:
                        col_name = f"{large_col_name}_{i}"
                        headers.insert(large_col_index + i, col_name)
                        row[col_name] = chunks[i]
                files_with_splits.add(output_filename)

            rows_buffer.append(row)
            row_count += 1
            file_row_counts[output_filename] += 1
            progress.update(task, advance=1)
            max_cell_length = max(max_cell_length, len(row[large_col_name]))

            if row_count % 50000 == 0:
                elapsed_time = time.time() - start_time
                progress.update(task, description=f"[cyan]Processing {output_filename}... Elapsed time: {elapsed_time:.2f} seconds")

        # Write remaining rows
        if rows_buffer:
            progress.log(f"[cyan]Saving {output_filename}...")
            writer = csv.DictWriter(output_file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows_buffer)
            output_file.close()
            console.log(f"[cyan]{output_filename} saved successfully.")

console.log(f"[green]Process completed.")
console.log(f"[green]The largest cell size was {max_cell_length} characters.")
