import os
import requests
import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook

# Constants
API_VERSION = '54.0'
INSTANCE_URL = 'https://specright-9558.my.salesforce.com'
SESSION_ID = '00D6A000000eg1p!AQEAQL6nWAkn_G7ry6SUtAPmUjqMBPs80kDYqYXrnu8LDKELkgyxwYBKXsjdDc401lpdODvj0APpM7qCmD5Dds84ZWxysiqm'

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {SESSION_ID}',
}

def auto_size_worksheet_columns(ws):
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name
        for cell in col:
            try:  # Necessary to avoid error on empty cells
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)  # Adding a little extra space
        ws.column_dimensions[column].width = adjusted_width

def read_objects_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]
		
def get_object_metadata(object_name):
    url = f"{INSTANCE_URL}/services/data/v{API_VERSION}/sobjects/{object_name}/describe"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error retrieving metadata for {object_name}: {response.text}")
        return None
    

def extract_relationships(fields):
    relationship_fields = [field for field in fields if field['type'] in ['reference']]
    relationship_data = []
    for field in relationship_fields:
        for referenceTo in field.get('referenceTo', []):
            relationship_data.append({
                'Field Name': field['name'],
                'Relationship Name': field.get('relationshipName', ''),
                'Related To': referenceTo
            })
    return relationship_data

def extract_picklist_values(fields):
    # Extract picklist values for fields that have them
    picklist_fields = [field for field in fields if 'picklistValues' in field and field['picklistValues']]
    picklist_data = []
    for field in picklist_fields:
        for value in field['picklistValues']:
            picklist_data.append({
                'Field Name': field['name'],
                'Picklist Value': value['value'],
                'Picklist Label': value.get('label', '')
            })
    return picklist_data

def extract_data_for_excel(metadata):
    # Basic Field Metadata
    fields_df = pd.DataFrame(metadata['fields'])
    basic_columns = ['name', 'label', 'type', 'defaultValue', 'length', 'precision', 'scale', 'unique']
    fields_df = fields_df[basic_columns]
    
    # Picklist Values
    picklist_data = extract_picklist_values(metadata['fields'])
    picklist_df = pd.DataFrame(picklist_data) if picklist_data else pd.DataFrame()
    
    # Relationships
    relationship_data = extract_relationships(metadata['fields'])
    relationship_df = pd.DataFrame(relationship_data) if relationship_data else pd.DataFrame()
    
    return fields_df, picklist_df, relationship_df

def save_to_excel(folder_path, object_name, fields_df, picklist_df, relationship_df):
    os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist
    file_path = os.path.join(folder_path, f"{object_name}_metadata.xlsx")
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        fields_df.to_excel(writer, sheet_name='Field Metadata', index=False)
        if not picklist_df.empty:
            picklist_df.to_excel(writer, sheet_name='Picklist Values', index=False)
        if not relationship_df.empty:
            relationship_df.to_excel(writer, sheet_name='Relationships', index=False)
        
        # Now adjust the column widths
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            auto_size_worksheet_columns(ws)

def main(file_path):
    folder_name = "ColgateOldMetadata"
    object_list = read_objects_from_file(file_path)
    for object_name in object_list:
        metadata = get_object_metadata(object_name)
        if metadata:
            fields_df, picklist_df, relationship_df = extract_data_for_excel(metadata)
            save_to_excel(folder_name, object_name, fields_df, picklist_df, relationship_df)
            print(f"Metadata for {object_name} saved to Excel folder.")

if __name__ == "__main__":
    file_path = 'objects.txt'  # Update this to your input file path
    main(file_path)
