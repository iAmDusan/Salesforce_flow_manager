import pandas as pd
import time

# Read the CSV file
df = pd.read_csv('file.csv')

# Get the unique case numbers
case_numbers = df['Case Number'].unique()

# Create a new DataFrame with columns for each possible user_case_fields value
user_case_fields = df['Custom Field Name'].unique()
new_columns = ['Case Number'] + list(user_case_fields)
new_df = pd.DataFrame(columns=new_columns)

# Fill in the new DataFrame with the data from the original DataFrame
start_time = time.time()
num_cases_processed = 0
num_total_cases = len(case_numbers)
for case_number in case_numbers:
    case_data = df[df['Case Number'] == case_number]
    row_data = {'Case Number': case_number}
    for field in user_case_fields:
        value = case_data[case_data['Custom Field Name'] == field]['Custom Field Value'].values
        if len(value) > 0:
            row_data[field] = value[0]
        else:
            row_data[field] = None
    new_df = pd.concat([new_df, pd.DataFrame(row_data, index=[0])], ignore_index=True)
    num_cases_processed += 1
    elapsed_time = time.time() - start_time
    remaining_time = (elapsed_time / num_cases_processed) * (num_total_cases - num_cases_processed)
    print(f"Processed {num_cases_processed}/{num_total_cases} cases. Elapsed time: {elapsed_time:.2f}s. Remaining time: {remaining_time:.2f}s.")

# Write the output to a new CSV file
new_df.to_csv('out.csv', index=False)

# Print a confirmation message
print('Output written to out.csv')
