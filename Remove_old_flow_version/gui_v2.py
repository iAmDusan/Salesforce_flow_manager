import sys
import os
import requests
import configparser
from prettytable import PrettyTable
from PyQt5.QtWidgets import (QApplication, QDialogButtonBox, QDialog, QMainWindow,
                             QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
                             QHBoxLayout, QFrame, QTextEdit, QScrollArea, QProgressBar,
                             QMessageBox, QCheckBox, QSplitter, QTreeWidget,
                             QTreeWidgetItem, QHeaderView, QAbstractItemView,
                             QFileDialog)
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt

script_dir = os.path.dirname(os.path.realpath(__file__))

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flow Management Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)

        self.config_path = None
        self.instance_url = None
        self.session_id = None
        self.headers = None
        self.config = None
        self.reverse_sort = False
        self.flow_vars = {}
        self.flow_definitions = {}

        self.create_widgets()
        self.load_last_config()

    def create_widgets(self):
        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        config_frame = QFrame()
        config_layout = QHBoxLayout(config_frame)
        self.config_path_label = QLabel("Config File Path:")
        self.config_path_entry = QLineEdit()
        self.load_config_button = QPushButton("Load Config")
        self.load_config_button.clicked.connect(self.load_config)
        config_layout.addWidget(self.config_path_label)
        config_layout.addWidget(self.config_path_entry)
        config_layout.addWidget(self.load_config_button)
        main_layout.addWidget(config_frame)

        action_frame = QFrame()
        action_layout = QHBoxLayout(action_frame)
        self.query_flows_button = QPushButton("Query All Flows")
        self.query_flows_button.clicked.connect(self.query_all_flows)
        action_layout.addWidget(self.query_flows_button)
        main_layout.addWidget(action_frame)

        splitter = QSplitter(Qt.Vertical)
        self.checkbox_frame = QFrame()
        checkbox_layout = QVBoxLayout(self.checkbox_frame)
        splitter.addWidget(self.checkbox_frame)

        output_frame = QFrame()
        output_layout = QVBoxLayout(output_frame)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Courier", 10))
        output_layout.addWidget(self.text_area)
        splitter.addWidget(output_frame)

        splitter.setSizes([600, 200])  # Adjust the sizes as needed
        splitter.setStretchFactor(0, 1)
        main_layout.addWidget(splitter)

        self.flow_tree = QTreeWidget()
        self.flow_tree.setColumnCount(4)
        self.flow_tree.setHeaderLabels(["Select", "Developer Name", "Latest Version", "Last Modified Date"])
        self.flow_tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.flow_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.flow_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.flow_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.flow_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.flow_tree.itemClicked.connect(self.on_flow_tree_click)
        self.flow_tree.itemExpanded.connect(self.handle_flow_item_expanded)
        self.checkbox_frame.layout().addWidget(self.flow_tree)

        self.status_bar = QLabel()
        self.status_bar.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(self.status_bar)

    def query_all_flows(self):
        if self.config:
            all_flows = self.retrieve_all_flows()
            if all_flows:
                if not hasattr(self, 'flow_tree'):
                    self.flow_tree = QTreeWidget()
                    self.flow_tree.setColumnCount(4)
                    self.flow_tree.setHeaderLabels(["Select", "Developer Name", "Latest Version", "Last Modified Date"])
                    self.flow_tree.setSelectionMode(QAbstractItemView.NoSelection)
                    self.flow_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
                    self.flow_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
                    self.flow_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
                    self.flow_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
                    self.flow_tree.itemClicked.connect(self.on_flow_tree_click)
                    self.checkbox_frame.layout().addWidget(self.flow_tree)
                    self.flow_vars = self.create_flow_checkboxes(all_flows)

                self.create_select_all_checkbox()

                self.update_flow_checkboxes(all_flows)

                for widget in self.checkbox_frame.children():
                    if isinstance(widget, QPushButton):
                        widget.deleteLater()

                delete_all_button = QPushButton("Delete All Versions of Selected Flows")
                delete_all_button.clicked.connect(self.delete_all_versions)
                self.checkbox_frame.layout().addWidget(delete_all_button)

                delete_inactive_button = QPushButton("Delete Inactive Versions of Selected Flows")
                delete_inactive_button.clicked.connect(self.delete_inactive_versions)
                self.checkbox_frame.layout().addWidget(delete_inactive_button)
                
                flow_info_button = QPushButton("Show Selected Flow Info")
                flow_info_button.clicked.connect(self.show_selected_flow_info)
                self.checkbox_frame.layout().addWidget(flow_info_button)


            else:
                self.text_area.append("No flows found to display.\n")
                self.scroll_to_bottom()
        else:
            QMessageBox.critical(self, "Error", "Please load a config file first.")

    def create_flow_checkboxes(self, all_flows):
        print("Creating flow checkboxes...")
        self.flow_tree.clear()
        self.flow_vars = {}
        self.flow_definitions = {}

        for flow in all_flows:
            flow_id = str(flow["Id"])
            flow_item = QTreeWidgetItem(self.flow_tree)

            # Populate the "Developer Name" column
            flow_item.setText(1, flow["DeveloperName"])

            # Populate the "Latest Version" column
            if 'LatestVersion' in flow and 'VersionNumber' in flow['LatestVersion']:
                latest_version_number = str(flow['LatestVersion']['VersionNumber'])
            else:
                latest_version_number = "N/A"
            flow_item.setText(2, latest_version_number)

            # Populate the "Last Modified Date" column
            flow_item.setText(3, flow["LastModifiedDate"].split('T')[0])

            checkbox = QCheckBox()
            checkbox.setText(flow["DeveloperName"])
            self.flow_vars[flow_id] = checkbox
            self.flow_tree.setItemWidget(flow_item, 0, checkbox)

            self.flow_definitions[flow["DeveloperName"]] = flow  # Store the flow definition data using the DeveloperName as the key

        self.flow_tree.setSortingEnabled(True)
        self.flow_tree.expandAll()  # Expand all items initially

        print(f"Number of flows processed: {len(all_flows)}")
        return self.flow_vars
            
    def set_status(self, message, color="black"):
        self.status_bar.setText(message)
        self.status_bar.setStyleSheet(f"color: {color}")

    def save_last_config_path(self):
        config_file = os.path.join(script_dir, "last_config.txt")
        with open(config_file, "w") as file:
            file.write(self.config_path)

    def load_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Config File", "", "INI Files (*.ini)")
        if file_path:
            self.config_path_entry.setText(file_path)
            self.config_path = file_path
            self.save_last_config_path()
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)
            self.instance_url = self.config.get('Salesforce', 'instance_url')
            self.session_id = self.config.get('Salesforce', 'session_id')
            self.headers = {'Authorization': f'Bearer {self.session_id}', 'Content-Type': 'application/json'}
            self.text_area.append(f"Loaded config file: {file_path}\n")
            self.update_connection_status()

    def load_last_config(self):
        config_file = os.path.join(script_dir, "last_config.txt")
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                config_path = file.read().strip()
                if config_path and os.path.exists(config_path):
                    self.config_path_entry.setText(config_path)
                    self.config_path = config_path
                    self.config = configparser.ConfigParser()
                    self.config.read(self.config_path)

                    self.instance_url = self.config.get('Salesforce', 'instance_url')
                    self.session_id = self.config.get('Salesforce', 'session_id')
                    self.headers = {
                        'Authorization': f'Bearer {self.session_id}',
                        'Content-Type': 'application/json'
                    }

                    self.text_area.append(f"Loaded config file: {config_path}\n")
                    self.query_flows_button.setEnabled(True)
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
        print("Retrieved flows:", data.get('records', []))
        return data.get('records', [])

    def retrieve_flow_definition_details(self, flow_api_name):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = f"SELECT Id, DeveloperName, LatestVersionId, LatestVersion.VersionNumber FROM FlowDefinition WHERE DeveloperName = '{flow_api_name}'"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        print(f"Flow Definition for '{flow_api_name}':", data['records'])
        if data['records']:
            return data['records'][0]
        else:
            return None

    def retrieve_flow_versions(self, flow_definition_info):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = f"SELECT Id, ApiVersion, VersionNumber, DefinitionId FROM Flow WHERE DefinitionId = '{flow_definition_info['Id']}' ORDER BY VersionNumber ASC"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        print(f"Flow Versions for '{flow_definition_info['DeveloperName']}':", data.get('records', []))
        return data.get('records', [])

    def delete_flow(self, flow_id):
        delete_flow_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/Flow/{flow_id}"
        response = requests.delete(delete_flow_url, headers=self.headers)

        if response.status_code == 400 and "DELETE_FAILED" in response.text:
            self.text_area.append(f"Skipping deletion of active flow version with ID '{flow_id}'.\n")
            self.scroll_to_bottom()
        else:
            response.raise_for_status()
            self.text_area.append(f"Flow with ID '{flow_id}' deleted successfully.\n")
            self.scroll_to_bottom()

    def display_flow_definition_info(self, flow_definition_info):
        self.text_area.append("FlowDefinition Details:\n")
        table = PrettyTable()
        table.field_names = ["ID", "Developer Name", "Latest Version ID", "Latest Version Number"]
        table.add_row([flow_definition_info['Id'], flow_definition_info['DeveloperName'], flow_definition_info['LatestVersionId'], flow_definition_info['LatestVersion']['VersionNumber']])
        self.text_area.append(table.get_string() + "\n")
        self.scroll_to_bottom()

    def display_flow_versions(self, flow_versions):
        self.text_area.append("\nFlow Versions:\n")
        table = PrettyTable()
        table.field_names = ["Index", "ID", "Version Number", "API Version", "Definition ID"]
        for index, fv in enumerate(flow_versions, start=1):
            table.add_row([index, fv['Id'], fv['VersionNumber'], fv['ApiVersion'], fv['DefinitionId']])
        self.text_area.append(table.get_string() + "\n")
        self.scroll_to_bottom()

    def get_selected_flows(self):
        selected_flows = []
        for i in range(self.flow_tree.topLevelItemCount()):
            flow_item = self.flow_tree.topLevelItem(i)
            checkbox = self.flow_tree.itemWidget(flow_item, 0)
            if checkbox and checkbox.isChecked():
                flow_id = next(key for key, value in self.flow_vars.items() if value == checkbox)
                selected_flows.append(flow_id)
        return selected_flows

    def display_active_flows(self, all_flows):
        self.text_area.append("\nActive Flows in the Org:\n")
        table = PrettyTable()
        table.field_names = ["Index", "ID", "Developer Name", "Active Version ID", "Active Version Number"]
        for index, flow in enumerate(all_flows, start=1):
            table.add_row([index, flow['Id'], flow['DeveloperName'], flow['LatestVersionId'], flow['LatestVersion']['VersionNumber']])
        self.text_area.append(table.get_string() + "\n")
        self.scroll_to_bottom()

    def on_flow_tree_click(self, item, column):
        if column == 0:
            if item.parent() is None:  # Flow item clicked
                checkbox = self.flow_tree.itemWidget(item, 0)
                if checkbox:
                    checkbox.setChecked(not checkbox.isChecked())
                    self.update_select_all_status()
            else:  # Version item clicked
                parent_item = item.parent()
                parent_checkbox = self.flow_tree.itemWidget(parent_item, 0)
                if parent_checkbox:
                    parent_checkbox.setChecked(not parent_checkbox.isChecked())
                    self.update_select_all_status()

    def update_select_all_status(self):
        all_checked = all(var.isChecked() for var in self.flow_vars.values())
        self.select_all_checkbox.setChecked(all_checked)

    def create_select_all_checkbox(self):
        if not hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox = QCheckBox("Select All")
            self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
            self.checkbox_frame.layout().addWidget(self.select_all_checkbox)

    def update_flow_checkboxes(self, all_flows):
        for flow in all_flows:
            flow_id = str(flow['Id'])
            checkbox = self.flow_vars.get(flow_id)
            if checkbox:
                item = self.flow_tree.findItems(flow["DeveloperName"], Qt.MatchExactly, 1)[0]
                self.flow_tree.setItemWidget(item, 0, checkbox)

    def toggle_select_all(self, state):
        is_selected = state == Qt.Checked
        for flow_id in self.flow_vars:
            self.flow_vars[flow_id].setChecked(is_selected)

    def get_user_selection(self, flow_versions):
            selection_dialog = QDialog(self)
            selection_dialog.setWindowTitle("Select Flow Versions")
            selection_dialog.setGeometry(100, 100, 400, 300)

            scroll_area = QScrollArea(selection_dialog)
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_area.setWidget(scroll_content)

            vars = {}
            for flow_version in flow_versions:
                checkbox = QCheckBox(f"Version {flow_version['VersionNumber']} - API {flow_version['ApiVersion']}")
                scroll_layout.addWidget(checkbox)
                vars[flow_version['Id']] = checkbox

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(selection_dialog.accept)
            button_box.rejected.connect(selection_dialog.reject)

            main_layout = QVBoxLayout(selection_dialog)
            main_layout.addWidget(scroll_area)
            main_layout.addWidget(button_box)

            if selection_dialog.exec() == QDialog.Accepted:
                selected_ids = [flow_id for flow_id, checkbox in vars.items() if checkbox.isChecked()]
                return selected_ids
            else:
                return []

    def delete_all_versions(self):
        selected_flows = self.get_selected_flows()
        if selected_flows:
            confirmation = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete all versions of the selected flows?", QMessageBox.Yes | QMessageBox.No)
            if confirmation == QMessageBox.Yes:
                deleted_flows = []
                not_deleted_flows = []
                for flow_id in selected_flows:
                    flow_api_name = self.flow_vars[flow_id].text()  # Get the flow API name from the checkbox text
                    flow_info = self.retrieve_flow_definition_details(flow_api_name)
                    if flow_info:
                        flow_versions = self.retrieve_flow_versions(flow_info)
                        if flow_versions:
                            all_versions_deleted = True
                            for version in flow_versions:
                                try:
                                    self.delete_flow(version['Id'])
                                except Exception as e:
                                    all_versions_deleted = False
                                    not_deleted_flows.append(f"{flow_info['DeveloperName']} (Version {version['VersionNumber']}): {str(e)}")
                            if all_versions_deleted:
                                deleted_flows.append(flow_info['DeveloperName'])
                        else:
                            not_deleted_flows.append(f"{flow_info['DeveloperName']}: No versions found")
                    else:
                        not_deleted_flows.append(f"{flow_api_name}: Flow definition not found")

                if deleted_flows:
                    self.text_area.append(f"Successfully deleted all versions of the following flows:\n{', '.join(deleted_flows)}\n")
                if not_deleted_flows:
                    self.text_area.append(f"Failed to delete the following flows:\n{', '.join(not_deleted_flows)}\n")
            else:
                self.text_area.append("Deletion cancelled.\n")
        else:
            self.text_area.append("No flows selected for deletion.\n")

        self.scroll_to_bottom()

    def show_selected_flow_info(self):
        selected_flows = self.get_selected_flows()
        if selected_flows:
            self.text_area.append("Selected Flow Information:\n")
            for flow_id in selected_flows:
                flow_api_name = self.flow_vars[flow_id].text()
                flow_info = self.retrieve_flow_definition_details(flow_api_name)
                if flow_info:
                    flow_versions = self.retrieve_flow_versions(flow_info)
                    version_count = len(flow_versions)
                    self.text_area.append(f"Flow: {flow_info['DeveloperName']}\n")
                    self.text_area.append(f"Total Versions: {version_count}\n")
                    self.text_area.append(f"Active Version: {flow_info['LatestVersion']['VersionNumber']}\n")
                    self.text_area.append("Version Details:\n")
                    for version in flow_versions:
                        self.text_area.append(f"- Version {version['VersionNumber']} (API {version['ApiVersion']})\n")
                    self.text_area.append("\n")
            self.scroll_to_bottom()
        else:
            QMessageBox.information(self, "No Flows Selected", "Please select at least one flow to show information.")

    def delete_inactive_versions(self):
        selected_flows = self.get_selected_flows()
        if selected_flows:
            confirmation = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete the inactive versions of the selected flows?", QMessageBox.Yes | QMessageBox.No)
            if confirmation == QMessageBox.Yes:
                deleted_flows = []
                not_deleted_flows = []
                for flow_id in selected_flows:
                    flow_api_name = self.flow_vars[flow_id].text()  # Get the flow API name from the checkbox text
                    flow_info = self.retrieve_flow_definition_details(flow_api_name)
                    if flow_info:
                        active_version_id = flow_info['LatestVersionId']
                        flow_versions = self.retrieve_flow_versions(flow_info)
                        if flow_versions:
                            inactive_versions_deleted = False
                            for version in flow_versions:
                                if version['Id'] != active_version_id:
                                    try:
                                        self.delete_flow(version['Id'])
                                        inactive_versions_deleted = True
                                    except Exception as e:
                                        not_deleted_flows.append(f"{flow_info['DeveloperName']} (Version {version['VersionNumber']}): {str(e)}")
                            if inactive_versions_deleted:
                                deleted_flows.append(flow_info['DeveloperName'])
                        else:
                            not_deleted_flows.append(f"{flow_info['DeveloperName']}: No versions found")

                if deleted_flows:
                    self.text_area.append(f"Successfully deleted inactive versions of the following flows:\n{', '.join(deleted_flows)}\n")
                if not_deleted_flows:
                    self.text_area.append(f"Failed to delete inactive versions of the following flows:\n{', '.join(not_deleted_flows)}\n")
            else:
                self.text_area.append("Deletion cancelled.\n")
        else:
            self.text_area.append("No flows selected for deletion.\n")

        self.scroll_to_bottom()

    def handle_flow_item_expanded(self, item):
        if item.childCount() == 0:  # Check if the item has no children
            flow_developer_name = item.text(1)  # Assuming the flow name is in column 1
            flow_data = self.flow_definitions.get(flow_developer_name)
            if flow_data:
                flow_info = self.retrieve_flow_definition_details(flow_developer_name)
                if flow_info:
                    flow_versions = self.retrieve_flow_versions(flow_info)
                    self.add_flow_versions_to_tree(item, flow_versions)
                else:
                    print("No flow info found for:", flow_developer_name)  # Error handling
            else:
                print("No data found for:", flow_developer_name)  # Error handling

    def add_flow_versions_to_tree(self, parent_item, flow_versions):
        for version in flow_versions:
            version_item = QTreeWidgetItem(parent_item)
            version_item.setText(1, f"Version {version['VersionNumber']}")
            version_item.setText(2, str(version['VersionNumber']))
            if 'LastModifiedDate' in version:
                version_item.setText(3, version['LastModifiedDate'].split('T')[0])
            else:
                version_item.setText(3, "N/A")
        parent_item.setExpanded(True)  # Expand the parent item to show the child items

    def scroll_to_bottom(self):
        cursor = self.text_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_area.setTextCursor(cursor)


def main():
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()