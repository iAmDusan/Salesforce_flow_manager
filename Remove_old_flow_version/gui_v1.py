import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
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
        self.geometry("1200x800")  # Increase the window width for better readability
        self.minsize(1000, 600)  # Set minimum size to avoid too small window

        self.config_path = None
        self.instance_url = None
        self.session_id = None
        self.headers = None
        self.config = None

        self.create_widgets()
        self.configure_grid()

    def create_widgets(self):
        # Create a frame for config file selection
        config_frame = ttk.LabelFrame(self, text="Config File Selection")
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.config_path_label = ttk.Label(config_frame, text="Config File Path:")
        self.config_path_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.config_path_entry = ttk.Entry(config_frame, width=50)
        self.config_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.load_config_button = ttk.Button(config_frame, text="Load Config", command=self.load_config)
        self.load_config_button.grid(row=0, column=2, padx=5, pady=5)

        # Create a frame for action buttons
        action_frame = ttk.LabelFrame(self, text="Actions")
        action_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.delete_inactive_button = ttk.Button(action_frame, text="Delete Inactive Versions", command=self.delete_inactive_versions, state=tk.DISABLED)
        self.delete_inactive_button.grid(row=0, column=0, padx=5, pady=5)

        self.query_flows_button = ttk.Button(action_frame, text="Query All Flows", command=self.query_all_flows, state=tk.DISABLED)
        self.query_flows_button.grid(row=0, column=1, padx=5, pady=5)

        # Create a frame for output area
        output_frame = ttk.LabelFrame(self, text="Output")
        output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.text_area = tk.Text(output_frame, wrap=tk.WORD, font=("Courier", 10))  # Use a monospace font for better alignment
        self.text_area.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.scrollbar = ttk.Scrollbar(output_frame, command=self.text_area.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.text_area.config(yscrollcommand=self.scrollbar.set)

        # Configure resizing behavior
        self.grid_rowconfigure(2, weight=1)  # Make row 2 (output frame) resizable
        self.grid_columnconfigure(0, weight=1)  # Make column 0 (main frame) resizable
        output_frame.grid_rowconfigure(0, weight=1)  # Make the text area expand vertically
        output_frame.grid_columnconfigure(0, weight=1)  # Make the text area expand horizontally

        # Create a status bar
        self.status_bar = ttk.Label(self, text="", anchor="w")
        self.status_bar.grid(row=3, column=0, padx=10, pady=5, sticky="ew")


    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

    def set_status(self, message, color="black"):
        self.status_bar.config(text=message, foreground=color)

    def load_config(self):
        file_path = filedialog.askopenfilename(title="Select Config File", filetypes=[("INI Files", "*.ini")])
        if file_path:
            self.config_path_entry.delete(0, tk.END)
            self.config_path_entry.insert(0, file_path)
            self.config_path = file_path
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)

            self.instance_url = self.config.get('Salesforce', 'instance_url')
            self.session_id = self.config.get('Salesforce', 'session_id')
            self.headers = {
                'Authorization': f'Bearer {self.session_id}',
                'Content-Type': 'application/json'
            }

            self.text_area.insert(tk.END, f"Loaded config file: {file_path}\n")
            self.delete_inactive_button.config(state=tk.NORMAL)
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
        query = "SELECT Id, DeveloperName, LatestVersionId, LatestVersion.VersionNumber, LatestVersion.Status FROM FlowDefinition"
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

    def get_user_selection(self, flow_versions):
        self.text_area.insert(tk.END, "Available Flow Versions:\n")
        table = PrettyTable()
        table.field_names = ["Index", "ID", "Version Number", "API Version", "Definition ID"]
        for index, fv in enumerate(flow_versions, start=1):
            table.add_row([index, fv['Id'], fv['VersionNumber'], fv['ApiVersion'], fv['DefinitionId']])
        self.text_area.insert(tk.END, table.get_string() + "\n")
        self.text_area.insert(tk.END, "Select the versions you want to delete (comma-separated indexes, e.g., '1,3,5' or 'all' for all versions): \n")
        self.scroll_to_bottom()

        user_input = self.get_user_input()
        if user_input == 'all':
            return [fv['Id'] for fv in flow_versions]
        else:
            selected_indexes = [int(index.strip()) for index in user_input.split(',') if index.strip().isdigit()]
            return [fv['Id'] for index, fv in enumerate(flow_versions, start=1) if index in selected_indexes]

    def get_user_input(self):
        user_input = simpledialog.askstring("User Input", "Enter your selection:")
        return user_input.lower() if user_input else ""

    def display_all_flows(self, all_flows):
        self.text_area.insert(tk.END, "\nAll Flows in the Org:\n")
        table = PrettyTable()
        table.field_names = ["Index", "ID", "Developer Name", "Latest Version ID", "Latest Version Number", "Active"]
        for index, flow in enumerate(all_flows, start=1):
            is_active = flow['LatestVersion']['Status'] == 'Active'
            table.add_row([index, flow['Id'], flow['DeveloperName'], flow['LatestVersionId'], flow['LatestVersion']['VersionNumber'], "Yes" if is_active else "No"])
        self.text_area.insert(tk.END, table.get_string() + "\n")
        self.scroll_to_bottom()

    def get_user_selection_for_flows(self, all_flows):
        self.text_area.insert(tk.END, "Select the flows you want to process by entering the index numbers (comma-separated, e.g., '1,3,5'): \n")
        self.scroll_to_bottom()
        user_input = self.get_user_input()
        selected_indexes = [int(index.strip()) for index in user_input.split(',') if index.strip().isdigit()]
        return [all_flows[index - 1]['DeveloperName'] for index in selected_indexes if 1 <= index <= len(all_flows)]

    def display_active_flows(self, all_flows):
        self.text_area.insert(tk.END, "\nActive Flows in the Org:\n")
        table = PrettyTable()
        table.field_names = ["Index", "ID", "Developer Name", "Active Version ID", "Active Version Number"]
        for index, flow in enumerate(all_flows, start=1):
            table.add_row([index, flow['Id'], flow['DeveloperName'], flow['LatestVersionId'], flow['LatestVersion']['VersionNumber']])
        self.text_area.insert(tk.END, table.get_string() + "\n")
        self.scroll_to_bottom()

    def delete_inactive_versions(self):
        all_flows = self.retrieve_all_flows()
        if all_flows:
            self.display_active_flows(all_flows)
            confirmation = messagebox.askyesno("Confirm Deletion", "Do you want to delete all inactive versions for the listed active flows?")
            if confirmation:
                for flow in all_flows:
                    self.delete_inactive_versions_for_flow(flow)
            else:
                self.text_area.insert(tk.END, "Deletion cancelled.\n")
                self.scroll_to_bottom()
        else:
            self.text_area.insert(tk.END, "No active flows found in the org.\n")
            self.scroll_to_bottom()

    def delete_inactive_versions_for_flow(self, flow_definition_info):
        flow_versions = self.retrieve_flow_versions(flow_definition_info)
        active_version_id = flow_definition_info['LatestVersionId']
        inactive_versions = [fv for fv in flow_versions if fv['Id'] != active_version_id]

        if inactive_versions:
            self.text_area.insert(tk.END, f"Deleting inactive versions for flow: {flow_definition_info['DeveloperName']}\n")
            self.scroll_to_bottom()
            for fv in inactive_versions:
                self.delete_flow(fv['Id'])
            self.text_area.insert(tk.END, f"Inactive versions deleted successfully for flow: {flow_definition_info['DeveloperName']}\n")
            self.scroll_to_bottom()
        else:
            self.text_area.insert(tk.END, f"No inactive versions found for flow: {flow_definition_info['DeveloperName']}\n")
            self.scroll_to_bottom()

    def query_all_flows(self):
        if self.config:
            all_flows = self.retrieve_all_flows()
            if all_flows:
                self.display_all_flows(all_flows)
                selected_flow_api_names = self.get_user_selection_for_flows(all_flows)
                if selected_flow_api_names:
                    self.text_area.insert(tk.END, f"Selected flows for processing: {', '.join(selected_flow_api_names)}\n")
                    self.scroll_to_bottom()
                    for flow_name in selected_flow_api_names:
                        self.process_selected_flow(flow_name)
                else:
                    self.text_area.insert(tk.END, "No flows selected for processing.\n")
                    self.scroll_to_bottom()
            else:
                self.text_area.insert(tk.END, "No flows found to display.\n")
                self.scroll_to_bottom()
        else:
            messagebox.showerror("Error", "Please load a config file first.")

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
