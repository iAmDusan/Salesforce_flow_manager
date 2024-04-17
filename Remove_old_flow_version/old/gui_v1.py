import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import requests
import configparser
from prettytable import PrettyTable

# Determine the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))

class App(tk.Tk):
    
    def __init__(self):
        super().__init__()
        self.title("Flow Management Tool")
        self.geometry("1200x800")
        self.minsize(1000, 600)

        self.config_path = None
        self.instance_url = None
        self.session_id = None
        self.headers = None
        self.config = None
        self.reverse_sort = False
        self.flow_vars = {}  # Ensure it's always a dictionary

        self.create_widgets()
        self.configure_grid()
        self.load_last_config()

    def create_widgets(self):
        config_frame = ttk.LabelFrame(self, text="Config File Selection")
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.config_path_label = ttk.Label(config_frame, text="Config File Path:")
        self.config_path_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.config_path_entry = ttk.Entry(config_frame, width=50)
        self.config_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.load_config_button = ttk.Button(config_frame, text="Load Config", command=self.load_config)
        self.load_config_button.grid(row=0, column=2, padx=5, pady=5)

        action_frame = ttk.LabelFrame(self, text="Actions")
        action_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.query_flows_button = ttk.Button(action_frame, text="Query All Flows", command=self.query_all_flows)
        self.query_flows_button.grid(row=0, column=0, padx=5, pady=5)

        self.paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned_window.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.checkbox_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.checkbox_frame, weight=1)
        self.output_frame = ttk.LabelFrame(self.paned_window, text="Output")
        self.paned_window.add(self.output_frame, weight=1)
        self.text_area = tk.Text(self.output_frame, wrap=tk.WORD, font=("Courier", 10), height=10)
        self.text_area.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.scrollbar = ttk.Scrollbar(self.output_frame, command=self.text_area.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_area.config(yscrollcommand=self.scrollbar.set)

        self.status_bar = ttk.Label(self, text="", anchor="w")
        self.status_bar.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

    def set_status(self, message, color="black"):
        self.status_bar.config(text=message, foreground=color)

    def save_last_config_path(self):
        config_file = os.path.join(script_dir, "last_config.txt")
        with open(config_file, "w") as file:
            file.write(self.config_path)

    def load_config(self):
        file_path = filedialog.askopenfilename(title="Select Config File", filetypes=[("INI Files", "*.ini")])
        if file_path:
            self.config_path_entry.delete(0, tk.END)
            self.config_path_entry.insert(0, file_path)
            self.config_path = file_path
            self.save_last_config_path()
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)
            self.instance_url = self.config.get('Salesforce', 'instance_url')
            self.session_id = self.config.get('Salesforce', 'session_id')
            self.headers = {'Authorization': f'Bearer {self.session_id}', 'Content-Type': 'application/json'}
            self.text_area.insert(tk.END, f"Loaded config file: {file_path}\n")
            self.update_connection_status()

    def load_last_config(self):
        config_file = os.path.join(script_dir, "last_config.txt")
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                config_path = file.read().strip()
                if config_path and os.path.exists(config_path):
                    self.config_path_entry.delete(0, tk.END)
                    self.config_path_entry.insert(0, config_path)
                    self.config_path = config_path
                    self.config = configparser.ConfigParser()
                    self.config.read(self.config_path)

                    self.instance_url = self.config.get('Salesforce', 'instance_url')
                    self.session_id = self.config.get('Salesforce', 'session_id')
                    self.headers = {
                        'Authorization': f'Bearer {self.session_id}',
                        'Content-Type': 'application/json'
                    }

                    self.text_area.insert(tk.END, f"Loaded config file: {config_path}\n")
                    self.query_flows_button.config(state=tk.NORMAL)
                    self.update_connection_status()

    def update_connection_status(self):
        try:
            org_info = self.get_org_info()
            is_sandbox = org_info.get('IsSandbox', False) or 'sandbox' in self.instance_url.lower()
            org_type = org_info.get('OrganizationType', 'Unknown')
            org_id = org_info.get('Id', 'Unknown')
            status_text = f"Connected to {org_type} Org ({org_id}) {'(Sandbox)' if is_sandbox else '(Production)'}"
            self.set_status(status_text, color="green")
        except Exception as e:
            self.set_status(f"Connection Error: {e}", color="red")

    def get_org_info(self):
        query_url = f"{self.instance_url}/services/data/v52.0/query?q=SELECT+Id,+Name,+IsSandbox,+OrganizationType+FROM+Organization"
        response = requests.get(query_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        org_info = data['records'][0]
        return org_info

    def retrieve_all_flows(self):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = "SELECT Id, DeveloperName, LatestVersionId, LatestVersion.VersionNumber, LastModifiedDate FROM FlowDefinition"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('records', [])

    def retrieve_flow_definition_details(self, flow_api_name):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = f"SELECT Id, DeveloperName, LatestVersionId, LatestVersion.VersionNumber FROM FlowDefinition WHERE DeveloperName = '{flow_api_name}'"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data['records'][0] if data.get('records') else None

    def retrieve_flow_versions(self, flow_definition_info):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = f"SELECT Id, ApiVersion, VersionNumber, DefinitionId FROM Flow WHERE DefinitionId = '{flow_definition_info['Id']}' ORDER BY VersionNumber ASC"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('records', [])

    def delete_flow(self, flow_id):
        delete_flow_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/Flow/{flow_id}"
        response = requests.delete(delete_flow_url, headers=self.headers)

        if response.status_code == 400 and "DELETE_FAILED" in response.text:
            self.text_area.insert(tk.END, f"Skipping deletion of active flow version with ID '{flow_id}'.\n")
            self.scroll_to_bottom()
        else:
            response.raise_for_status()
            self.text_area.insert(tk.END, f"Flow with ID '{flow_id}' deleted successfully.\n")
            self.scroll_to_bottom()

    def display_flow_definition_info(self, flow_definition_info):
        self.text_area.insert(tk.END, "FlowDefinition Details:\n")
        table = PrettyTable()
        table.field_names = ["ID", "Developer Name", "Latest Version ID", "Latest Version Number"]
        table.add_row([flow_definition_info['Id'], flow_definition_info['DeveloperName'], flow_definition_info['LatestVersionId'], flow_definition_info['LatestVersion']['VersionNumber']])
        self.text_area.insert(tk.END, table.get_string() + "\n")
        self.scroll_to_bottom()

    def display_flow_versions(self, flow_versions):
        self.text_area.insert(tk.END, "\nFlow Versions:\n")
        table = PrettyTable()
        table.field_names = ["Index", "ID", "Version Number", "API Version", "Definition ID"]
        for index, fv in enumerate(flow_versions, start=1):
            table.add_row([index, fv['Id'], fv['VersionNumber'], fv['ApiVersion'], fv['DefinitionId']])
        self.text_area.insert(tk.END, table.get_string() + "\n")
        self.scroll_to_bottom()

    def get_selected_flows(self, all_flows):
        selected_flows = [flow["DeveloperName"] for flow in all_flows if self.flow_vars[flow["Id"]].get()]
        return selected_flows

    def display_active_flows(self, all_flows):
        self.text_area.insert(tk.END, "\nActive Flows in the Org:\n")
        table = PrettyTable()
        table.field_names = ["Index", "ID", "Developer Name", "Active Version ID", "Active Version Number"]
        for index, flow in enumerate(all_flows, start=1):
            table.add_row([index, flow['Id'], flow['DeveloperName'], flow['LatestVersionId'], flow['LatestVersion']['VersionNumber']])
        self.text_area.insert(tk.END, table.get_string() + "\n")
        self.scroll_to_bottom()

    def query_all_flows(self):
        if self.config:
            all_flows = self.retrieve_all_flows()
            if all_flows:
                if not hasattr(self, 'flow_frame'):
                    # Create the initial flow frame and Treeview
                    self.flow_frame = ttk.Frame(self.checkbox_frame)
                    self.flow_frame.pack(fill=tk.BOTH, expand=True)
                    self.flow_vars = self.create_flow_checkboxes(all_flows)  # Create checkboxes

                self.create_select_all_checkbox()  # This will create the "Select All" checkbox

                # Update existing checkboxes
                self.update_flow_checkboxes(all_flows)  

                # Assuming you need to recreate the "Process Selected Flows" button each time:
                for widget in self.checkbox_frame.winfo_children():
                    if isinstance(widget, ttk.Button):  # Target only the button
                        widget.destroy()

                process_button = ttk.Button(self.checkbox_frame, text="Process Selected Flows", command=lambda: self.process_selected_flows(all_flows))
                process_button.pack(pady=5)                
            else:
                self.text_area.insert(tk.END, "No flows found to display.\n")
                self.scroll_to_bottom()
        else:
            messagebox.showerror("Error", "Please load a config file first.")

    def create_flow_checkboxes(self, all_flows):
        if hasattr(self, 'flow_frame'):
            self.flow_frame.destroy()
        self.flow_frame = ttk.Frame(self.checkbox_frame)
        self.flow_frame.pack(fill=tk.BOTH, expand=True)

        # Create the Treeview
        self.flow_treeview = ttk.Treeview(self.flow_frame, columns=("Select", "DeveloperName", "LatestVersionNumber", "LastModifiedDate"), show="headings")
        self.flow_treeview.heading("Select", text="Select")
        self.flow_treeview.column("Select", width=50, anchor="center")
        self.flow_treeview.heading("DeveloperName", text="Developer Name")
        self.flow_treeview.column("DeveloperName", width=200)
        self.flow_treeview.heading("LatestVersionNumber", text="Latest Version")
        self.flow_treeview.column("LatestVersionNumber", width=100, anchor="center")
        self.flow_treeview.heading("LastModifiedDate", text="Last Modified Date")
        self.flow_treeview.column("LastModifiedDate", width=150)
        self.flow_treeview.pack(fill=tk.BOTH, expand=True)

        # Populate checkboxes with flow data
        for flow in all_flows:
            flow_id = str(flow["Id"])  # Convert ID to string
            checkbox_value = ""  # Start with an unchecked box
            self.flow_vars[flow_id] = tk.BooleanVar(value=False)
            self.flow_treeview.insert("", "end", iid=flow_id, values=(checkbox_value, flow["DeveloperName"], flow["LatestVersion"]["VersionNumber"], flow["LastModifiedDate"].split('T')[0]))
        
        for col in self.flow_treeview['columns']:
            self.flow_treeview.heading(col, text=col, command=lambda _col=col: self.sort_treeview(_col))

        # Bind the Treeview click event
        self.flow_treeview.bind('<ButtonRelease-1>', self.on_treeview_click)

        return self.flow_vars

    def on_treeview_click(self, event):
        region = self.flow_treeview.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.flow_treeview.identify_row(event.y)
            column = self.flow_treeview.identify_column(event.x)
            if column == "#1":  # Only toggle if the first column is clicked
                current_value = self.flow_treeview.item(row_id, 'values')[0]
                new_value = "" if current_value == "✓" else "✓"
                self.flow_treeview.item(row_id, values=(new_value,) + self.flow_treeview.item(row_id, 'values')[1:])
                self.flow_vars[row_id].set(not self.flow_vars[row_id].get())
                self.update_select_all_status()  # Optionally, update the "Select All" checkbox

    def update_select_all_status(self):
        all_checked = all(var.get() for var in self.flow_vars.values())
        self.select_all_var.set(all_checked)
        # Update the "Select All" checkbox's visual state
        self.select_all_checkbox.config(text="Select All" if all_checked else "Select All")

    def create_select_all_checkbox(self):
        # Create "Select All" checkbox only if it doesn't exist
        if not hasattr(self, 'select_all_checkbox'):
            self.select_all_var = tk.BooleanVar(value=False)
            self.select_all_checkbox = ttk.Checkbutton(self.flow_frame, text="Select All", variable=self.select_all_var, command=self.toggle_select_all)
            self.select_all_checkbox.pack(pady=5)

    def update_flow_checkboxes(self, all_flows):
        for flow in all_flows:
            flow_id = str(flow['Id'])  # Convert ID to string
            checkbox_value = "✓" if self.flow_vars.get(flow_id).get() else ""
            self.flow_treeview.item(flow_id, values=(checkbox_value, flow["DeveloperName"], flow["LatestVersion"]["VersionNumber"], flow["LastModifiedDate"].split('T')[0]))

    def toggle_select_all(self):
        is_selected = self.select_all_var.get()
        for flow_id in self.flow_vars:
            self.flow_vars[flow_id].set(is_selected)
            checkbox_value = "✓" if is_selected else ""
            self.flow_treeview.item(flow_id, values=(checkbox_value,) + self.flow_treeview.item(flow_id, 'values')[1:])

    def sort_treeview(self, column):
        # Retrieve the data in the form of a list of tuples (value, item ID)
        data = [(self.flow_treeview.set(child, column), child) for child in self.flow_treeview.get_children('')]

        # Determine whether to sort numerically or alphabetically
        # You could enhance this by checking if all retrieved values are numeric and deciding based on that
        data.sort(key=lambda t: float(t[0]) if t[0].isdigit() else t[0], reverse=self.reverse_sort)

        # Reorder the items in the Treeview
        for index, (val, k) in enumerate(data):
            self.flow_treeview.move(k, '', index)

        # Reverse the sort next time
        self.reverse_sort = not self.reverse_sort

    def get_user_selection(self, flow_versions):
        # Create a Toplevel window to hold the selection widgets
        selection_window = tk.Toplevel(self)
        selection_window.title("Select Flow Versions")
        selection_window.geometry("400x300")

        # Scrollable area to hold checkboxes
        canvas = tk.Canvas(selection_window)
        scrollbar = ttk.Scrollbar(selection_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Checkboxes for each flow version
        vars = {}
        for flow_version in flow_versions:
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(scrollable_frame, text=f"Version {flow_version['VersionNumber']} - API {flow_version['ApiVersion']}", variable=var)
            checkbox.pack(anchor='w', padx=10, pady=5)
            vars[flow_version['Id']] = var

        # Button to submit selection
        submit_button = ttk.Button(selection_window, text="Submit Selection", command=selection_window.destroy)
        submit_button.pack(pady=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Wait for the user to close the window
        self.wait_window(selection_window)

        # Collect all selected ids
        selected_ids = [flow_id for flow_id, var in vars.items() if var.get()]
        return selected_ids

    def process_selected_flows(self, all_flows):
        selected_flow_api_names = self.get_selected_flows(all_flows)
        
        if selected_flow_api_names:
            self.text_area.insert(tk.END, f"Selected flows for processing: {', '.join(selected_flow_api_names)}\n")
            self.scroll_to_bottom()

            progress_bar = ttk.Progressbar(self, length=200, mode='determinate')
            progress_bar.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
            progress_bar['maximum'] = len(selected_flow_api_names)
            progress_bar['value'] = 0

            for index, flow_name in enumerate(selected_flow_api_names, start=1):
                self.process_selected_flow(flow_name)
                progress_bar['value'] = index
                self.update_idletasks()

            progress_bar.grid_remove()
        else:
            self.text_area.insert(tk.END, "No flows selected for processing.\n")
            self.scroll_to_bottom()

    def process_selected_flow(self, flow_api_name):
        flow_definition_info = self.retrieve_flow_definition_details(flow_api_name)
        if flow_definition_info:
            self.display_flow_definition_info(flow_definition_info)
            flow_versions = self.retrieve_flow_versions(flow_definition_info)
            if flow_versions:
                self.display_flow_versions(flow_versions)
                selected_ids = self.get_user_selection(flow_versions)
                if selected_ids:
                    confirmation = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected flow versions?")
                    if confirmation:
                        for flow_id in selected_ids:
                            self.delete_flow(flow_id)
                        self.text_area.insert(tk.END, "Selected flow versions deleted successfully!\n")
                        self.scroll_to_bottom()
                    else:
                        self.text_area.insert(tk.END, "Deletion cancelled.\n")
                        self.scroll_to_bottom()
                else:
                    self.text_area.insert(tk.END, "No flow versions selected.\n")
                    self.scroll_to_bottom()
            else:
                self.text_area.insert(tk.END, "No flow versions found for this flow.\n")
                self.scroll_to_bottom()
        else:
            self.text_area.insert(tk.END, f"No FlowDefinition found for {flow_api_name}.\n")
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        self.text_area.see(tk.END)

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()