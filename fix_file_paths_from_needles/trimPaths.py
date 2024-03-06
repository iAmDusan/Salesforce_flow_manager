import os
import pandas as pd

# get the current working directory
cwd = os.getcwd()

# construct the file path to the CSV file
csv_file_path = os.path.join(cwd, 'file.csv')

# read the CSV file into a pandas DataFrame
df = pd.read_csv(csv_file_path)

# define the maximum depth of folders to keep in the file_path column. The drive letter itself is considered level 1
max_depth = 4

# create a function to trim the file_path column
def trim_file_path(file_path):
    # split the file_path string into its individual folders. leading escape char required since we are looking for each \
    folders = file_path.split('\\')
    # only go as deep as the max_depth
    trimmed_folders = folders[:max_depth]
    # join the trimmed folders back together with backslashes. leading escape char required again
    trimmed_file_path = '\\'.join(trimmed_folders)
    # add the final backslash to the end of the trimmed_file_path string. leading escape char required once again
    trimmed_file_path += '\\'
    # return the trimmed_file_path string
    return trimmed_file_path

# apply the trim_file_path function to the file_path column
df['file_path'] = df['file_path'].apply(trim_file_path)

# construct the file path to the new CSV file in the current working dir
new_csv_file_path = os.path.join(cwd, 'new_file.csv')

# write the updated DataFrame back to the new CSV file
df.to_csv(new_csv_file_path, index=False)
