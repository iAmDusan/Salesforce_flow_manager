# This file scrubs and splits case notes into 500k row files

import csv
import os
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
    """cell_content[i:i+MAX_CELL_SIZE]: This is a slice of the cell_content string. In Python, you can access a part of a list or string (called a slice) by using the syntax list[start:stop]. In this case, start is i and stop is i + MAX_CELL_SIZE. So for each i, you get the chunk of cell_content starting at index i and ending at index i + MAX_CELL_SIZE - 1 (or the end of the string, whichever comes first)."""
    return [cell_content[i:i+MAX_CELL_SIZE] for i in range(0, len(cell_content), MAX_CELL_SIZE)]

large_col_name = "litify_pm__lit_Note__c"
large_col_index = None  # This will be determined later
max_splits = 0

with open(INPUT_FILE, 'r', encoding='utf-8') as input_file:
    reader = csv.reader(input_file)
    headers = next(reader)
    large_col_index = headers.index(large_col_name)

    row_count = 0
    file_count = 1
    output_file = None
    file_row_counts = {}
    files_with_splits = set()

    progress = Progress("[progress.description]{task.description}",
                        "[progress.percentage]{task.percentage:>3.0f}%",
                        "[progress.bar]{task.completed}/{task.total}")

    max_cell_length = 0

    with progress:
        file_progress = progress.add_task("[cyan]Processing...", total=MAX_ROWS_PER_FILE)

        for row in reader:
            if row_count % MAX_ROWS_PER_FILE == 0:
                if output_file is not None:
                    output_file.close()
                output_filename = f'{OUTPUT_DIR}/{os.path.splitext(INPUT_FILE)[0]}_{file_count}.csv'
                output_file = open(output_filename, 'w', newline='', encoding='utf-8')
                writer = csv.writer(output_file)
                file_count += 1
                file_row_counts[output_filename] = 0
                writer.writerow(headers) # write headers to each out file
                progress.update(file_progress, completed=0)  # Reset progress for the new file
            if len(row[large_col_index]) > MAX_CELL_SIZE:
                chunks = split_large_cell(row[large_col_index])
                for i in range(len(chunks)):
                    if i > max_splits:
                        max_splits = i
                    if i == 0:
                        row[large_col_index] = chunks[i]
                    else:
                        row.insert(large_col_index + i, chunks[i])
                files_with_splits.add(output_filename)
            writer.writerow(row)
            row_count += 1
            file_row_counts[output_filename] += 1
            progress.update(file_progress, advance=1)
            max_cell_length = max(max_cell_length, len(row[large_col_index]))

    if output_file is not None:
        output_file.close()

console.print(f'Processed a total of [bold magenta]{row_count}[/bold magenta] rows.', style="green")
console.print(f'Generated [bold magenta]{file_count - 1}[/bold magenta] output files.', style="green")
console.print('The following files had cells in the "litify_pm__lit_Note__c" column split across multiple columns:')
for filename in files_with_splits:
    console.print(f'- {filename}', style="yellow")
console.print('Here are the number of rows in each output file:')
for filename, count in file_row_counts.items():
    console.print(f'- {filename}: [bold cyan]{count}[/bold cyan] rows', style="green")
console.print(f'The largest cell size encountered was [bold magenta]{max_cell_length}[/bold magenta] characters.', style="green")