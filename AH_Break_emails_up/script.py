import pandas as pd

# Read the data from the CSV file
df = pd.read_csv('input.csv')

# Define the columns you want in the final output
output_columns = ['Legacy_names_id__c', 'Business_Email__c', 'Website', 'litify_pm__Email__c', 'Other_Email__c', 'Additional_Online_Accounts__c']
result_df = pd.DataFrame(columns=output_columns)

# Iterate over each unique Legacy_names_id__c
for legacy_id in df['Legacy_names_id__c'].unique():
    # Get the rows with the current Legacy_names_id__c
    rows = df[df['Legacy_names_id__c'] == legacy_id]

    new_row = {'Legacy_names_id__c': legacy_id}

    # Iterate over the columns you want to process
    for column in ['Business_Email__c', 'Website', 'litify_pm__Email__c', 'Other_Email__c']:
        # Get the values for the current column
        values = rows[rows['sfdc_field'] == column]['value'].values

        if len(values) > 0:
            # Save the first value in the new row
            new_row[column] = values[0]

            # Save the remaining values as comma-separated string in Additional_Online_Accounts__c
            if len(values) > 1:
                if 'Additional_Online_Accounts__c' not in new_row:
                    new_row['Additional_Online_Accounts__c'] = ''
                new_row['Additional_Online_Accounts__c'] += ', '.join(values[1:]) + ', '

    # Include values from the 'Additional_Online_Accounts__c' column
    additional_values = rows[rows['sfdc_field'] == 'Additional_Online_Accounts__c']['value'].values
    if len(additional_values) > 0:
        if 'Additional_Online_Accounts__c' not in new_row:
            new_row['Additional_Online_Accounts__c'] = ''
        new_row['Additional_Online_Accounts__c'] += ', '.join(additional_values) + ', '

    # Remove the trailing comma and space from Additional_Online_Accounts__c
    if 'Additional_Online_Accounts__c' in new_row:
        new_row['Additional_Online_Accounts__c'] = new_row['Additional_Online_Accounts__c'].rstrip(', ')

    # Append the new row to the result DataFrame
    result_df = result_df.append(new_row, ignore_index=True)

# Save the flattened DataFrame to a new CSV file
result_df.to_csv('flattened_data.csv', index=False)
