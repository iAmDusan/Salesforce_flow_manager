import sys
import os
import requests
import configparser
import logging
from flow_backup_manager import FlowBackupManager
from salesforce_api import SalesforceAPI
from prettytable import PrettyTable
from PyQt5.QtWidgets import (
    QApplication, QDialogButtonBox, QDialog, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QTextEdit, QScrollArea, QProgressBar, QMessageBox, QCheckBox, QSplitter, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QAbstractItemView, QFileDialog, QComboBox
)
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt

script_dir = os.path.dirname(os.path.realpath(__file__))

class App(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flow Management Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)
        self.salesforce_api = None
        self.config_path = None
        self.instance_url = None
        self.session_id = None
        self.headers = None
        self.config = None
        self.reverse_sort = False
        self.flow_vars = {}
        self.progress_bar = None  # Add progress bar attribute
        self.backup_manager = None
        self.splitter = None  # Add splitter attribute
        self.create_widgets()
        self.load_last_config()
        self.setup_logging()



    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def create_widgets(self):
        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Config Frame
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

        # Action Frame
        action_frame = QFrame()
        action_layout = QHBoxLayout(action_frame)
        self.query_flows_button = QPushButton("Query All Flows")
        self.query_flows_button.clicked.connect(self.query_all_flows)
        self.filter_combobox = QComboBox()
        self.filter_combobox.addItems(["All", "Active", "Inactive"])
        self.filter_combobox.currentIndexChanged.connect(self.apply_filter)
        action_layout.addWidget(self.query_flows_button)
        action_layout.addWidget(self.filter_combobox)
        main_layout.addWidget(action_frame)
        
        # Create backup and restore buttons
        backup_button = QPushButton("Backup Selected Flows")
        backup_button.clicked.connect(self.backup_selected_flows)
        restore_button = QPushButton("Restore Flow")
        restore_button.clicked.connect(self.restore_flow)

        button_layout = QHBoxLayout()
        button_layout.addWidget(backup_button)
        button_layout.addWidget(restore_button)

        main_layout.addLayout(button_layout)


        # Splitter for Checkbox Frame and Output Frame
        self.splitter = QSplitter(Qt.Vertical)
        self.checkbox_frame = QFrame()
        checkbox_layout = QVBoxLayout(self.checkbox_frame)
        self.splitter.addWidget(self.checkbox_frame)

        # Flow Tree Widget
        self.flow_tree = QTreeWidget()
        self.flow_tree.setColumnCount(5)
        self.flow_tree.setHeaderLabels(["Select", "Developer Name", "Latest Version", "Last Modified Date", "Is Active"])
        self.flow_tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.flow_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.flow_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.flow_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.flow_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.flow_tree.header().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        checkbox_layout.addWidget(self.flow_tree)

        # Output Frame
        output_frame = QFrame()
        output_layout = QVBoxLayout(output_frame)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Courier", 10))
        output_layout.addWidget(self.text_area)
        self.splitter.addWidget(output_frame)
        self.splitter.setSizes([600, 200])
        self.splitter.setStretchFactor(0, 1)
        main_layout.addWidget(self.splitter)

        # Status Bar and Progress Bar
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        self.status_bar = QLabel()
        self.status_bar.setAlignment(Qt.AlignLeft)
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()  # Initially hide the progress bar 
        status_layout.addWidget(self.status_bar)
        status_layout.addWidget(self.progress_bar)
        main_layout.addWidget(status_frame)

        # Create Select All checkbox after flow_tree is initialized
        self.select_all_checkbox = None
        self.create_select_all_checkbox()
        


    def apply_filter(self, index):
        filter_text = self.filter_combobox.currentText()
        for i in range(self.flow_tree.topLevelItemCount()):
            item = self.flow_tree.topLevelItem(i)
            is_active = item.text(4) == "Yes"
            if filter_text == "All" or (filter_text == "Active" and is_active) or (filter_text == "Inactive" and not is_active):
                item.setHidden(False)
            else:
                item.setHidden(True)


    def backup_selected_flows(self):
        selected_flows = self.get_selected_flows()
        if not selected_flows:
            QMessageBox.information(self, "No Flows Selected", "Please select at least one flow to backup.")
            return

        backup_dir = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if backup_dir:
            self.backup_manager.backup_flows(selected_flows, backup_dir, self.text_area, self.find_flow_item_by_id, self.retrieve_flow_definition_details, self.retrieve_flow_versions)
        else:
            self.text_area.append("Backup cancelled.\n")

        self.scroll_to_bottom()


    def restore_flow(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Flow Backup File", "", "JSON Files (*.json);;XML Files (*.xml)")
        if file_path:
            try:
                self.backup_manager.restore_flow_definition(file_path)
                self.text_area.append(f"Flow restored successfully from {file_path}\n")
            except Exception as e:
                self.text_area.append(f"Error restoring flow: {str(e)}\n")
            self.scroll_to_bottom()


    def query_all_flows(self):
        if self.config:
            self.progress_bar.show()  # Show progress bar during query
            self.progress_bar.setValue(0)
            all_flows = self.salesforce_api.retrieve_all_flows()
            if all_flows:
                self.flow_tree.clear() 
                self.flow_vars = self.create_flow_checkboxes(all_flows)
                self.create_select_all_checkbox()
                self.update_flow_checkboxes(all_flows)
                self.apply_filter(self.filter_combobox.currentIndex())  # Apply current filter

                # Removing existing buttons before creating new ones
                for widget in self.checkbox_frame.children():
                    if isinstance(widget, QPushButton):
                        widget.deleteLater()

                # Create a QHBoxLayout to hold the buttons
                button_layout = QHBoxLayout()

                # Creating buttons
                delete_all_except_active_button = QPushButton("Delete All Except Active")
                delete_all_except_active_button.setFixedHeight(25)  # Reduce the fixed height of the button
                delete_all_except_active_button.clicked.connect(self.delete_all_versions_except_active)
                button_layout.addWidget(delete_all_except_active_button)

                delete_all_except_latest_button = QPushButton("Delete All Except Latest")
                delete_all_except_latest_button.setFixedHeight(25)  # Reduce the fixed height of the button
                delete_all_except_latest_button.clicked.connect(self.delete_all_versions_except_latest)
                button_layout.addWidget(delete_all_except_latest_button)

                delete_entire_flowdefinition_button = QPushButton("Delete Entire Flow")
                delete_entire_flowdefinition_button.setFixedHeight(25)  # Reduce the fixed height of the button
                delete_entire_flowdefinition_button.clicked.connect(self.delete_entire_flowdefinition)
                button_layout.addWidget(delete_entire_flowdefinition_button)

                flow_info_button = QPushButton("Show Selected Flow Info")
                flow_info_button.setFixedHeight(25)  # Reduce the fixed height of the button
                flow_info_button.clicked.connect(self.show_selected_flow_info)
                button_layout.addWidget(flow_info_button)

                # Add the button layout to the checkbox_frame
                self.checkbox_frame.layout().addLayout(button_layout)

                # Adjust the stretch factor of the splitter to give more space to the flow tree
                self.splitter.setStretchFactor(0, 4)  # Increase the stretch factor for the flow tree
                self.splitter.setStretchFactor(1, 1)  # Decrease the stretch factor for the output area
            else:
                self.text_area.append("No flows found to display.\n")
                self.scroll_to_bottom()
        else:
            QMessageBox.critical(self, "Error", "Please load a config file first.")

    def create_flow_checkboxes(self, all_flows):
        self.flow_tree.clear()
        self.flow_vars = {}

        for flow in all_flows:
            flow_id = str(flow["Id"])
            flow_item = QTreeWidgetItem(self.flow_tree)

            flow_item.setText(1, flow["DeveloperName"])
            flow_item.setText(3, flow["LastModifiedDate"].split('T')[0])

            # Convert version number to an integer and pad it for display
            latest_version_number = int(flow["LatestVersion"]["VersionNumber"])
            flow_item.setText(2, str(latest_version_number).zfill(3))  # Pad with zeros for sorting
            flow_item.setData(2, Qt.UserRole, latest_version_number)  # Store the integer for internal use

            latest_version_id = flow["LatestVersionId"]
            active_version_id = flow.get("ActiveVersionId", "")
            is_active = latest_version_id == active_version_id
            flow_item.setText(4, "Yes" if is_active else "No")

            if is_active:
                font = flow_item.font(4)
                font.setBold(True)
                flow_item.setFont(4, font)

            checkbox = QCheckBox()
            self.flow_vars[flow_id] = checkbox
            self.flow_tree.setItemWidget(flow_item, 0, checkbox)

        self.flow_tree.setSortingEnabled(True)
        # Make sure to sort after the items have been added and UserRole data has been set
        self.flow_tree.sortByColumn(2, Qt.AscendingOrder)
        self.flow_tree.expandAll()

        return self.flow_vars



    def update_select_all_status(self):
        all_checked = all(checkbox.isChecked() for checkbox in self.flow_vars.values())
        self.select_all_checkbox.setChecked(all_checked)

    def create_select_all_checkbox(self):
        if not self.select_all_checkbox:
            select_all_checkbox = QCheckBox("Select All")
            select_all_checkbox.stateChanged.connect(self.handle_select_all)
            self.checkbox_frame.layout().insertWidget(0, select_all_checkbox)
            self.select_all_checkbox = select_all_checkbox

    def handle_select_all(self, state):
        filter_text = self.filter_combobox.currentText()
        for i in range(self.flow_tree.topLevelItemCount()):
            item = self.flow_tree.topLevelItem(i)
            is_active = item.text(4) == "Yes"
            if not item.isHidden() and ((filter_text == "All") or
                                        (filter_text == "Active" and is_active) or
                                        (filter_text == "Inactive" and not is_active)):
                checkbox = self.flow_tree.itemWidget(item, 0)
                checkbox.setChecked(state == Qt.Checked)

    def update_flow_checkboxes(self, all_flows):
        count = 0
        total = len(all_flows)
        for flow in all_flows:
            flow_id = str(flow['Id'])
            checkbox = self.flow_vars.get(flow_id)
            count += 1
            self.progress_bar.setValue(int(count / total * 100))  # Update progress bar 
            if checkbox:
                item = self.flow_tree.findItems(flow["DeveloperName"], Qt.MatchExactly, 1)[0]
                self.flow_tree.setItemWidget(item, 0, checkbox)



    def retrieve_all_flows(self):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = "SELECT Id, DeveloperName, LatestVersionId, ActiveVersionId, ActiveVersion.VersionNumber, LatestVersion.VersionNumber, LastModifiedDate FROM FlowDefinition"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('records', [])

    def retrieve_flow_definition_details(self, flow_api_name):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = f"SELECT Id, DeveloperName, LatestVersionId, ActiveVersionId, ActiveVersion.VersionNumber, LatestVersion.VersionNumber FROM FlowDefinition WHERE DeveloperName = '{flow_api_name}'"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        if data['records']:
            return data['records'][0]
        else:
            self.text_area.append(f"No FlowDefinition found for {flow_api_name}.\n")
            self.scroll_to_bottom()
            return None

    def retrieve_flow_versions(self, flow_definition_info):
        url = f"{self.instance_url}/services/data/v52.0/tooling/query/"
        query = f"SELECT Id, ApiVersion, VersionNumber, DefinitionId FROM Flow WHERE DefinitionId = '{flow_definition_info['Id']}' ORDER BY VersionNumber ASC"
        encoded_query = requests.utils.quote(query)
        full_url = f"{url}?q={encoded_query}"
        response = requests.get(full_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('records', [])



    def get_selected_flows(self):
        selected_flows = [flow_id for flow_id, checkbox in self.flow_vars.items() if checkbox.isChecked()]
        return selected_flows

    def display_flow_versions(self, flow_definition_info):
        flow_versions = self.salesforce_api.retrieve_flow_versions(flow_definition_info)
        table = PrettyTable()
        table.field_names = ["Index", "ID", "Version Number", "API Version", "Definition ID"]
        for index, fv in enumerate(flow_versions, start=1):
            table.add_row([index, fv['Id'], fv['VersionNumber'], fv['ApiVersion'], fv['DefinitionId']])
        self.text_area.append(table.get_string() + "\n")

    def show_selected_flow_info(self):
        selected_flows = self.get_selected_flows()
        if not selected_flows:
            QMessageBox.information(self, "No Flows Selected", "Please select at least one flow to show information.")
            return

        self.text_area.clear()
        self.text_area.append("Selected Flow Information:\n")

        for flow_id in selected_flows:
            flow_item = self.find_flow_item_by_id(flow_id)
            if not flow_item:
                self.text_area.append(f"Error: Flow item not found for ID {flow_id}.\n")
                continue

            flow_api_name = flow_item.text(1)  # Assuming API name is in the second column
            if not flow_api_name.strip():
                self.text_area.append(f"Error: No API name provided for flow ID {flow_id}.\n")
                continue

            flow_info = self.retrieve_flow_definition_details(flow_api_name)
            if flow_info:
                self.text_area.append(f"Flow Name: {flow_api_name}\n")
                self.display_flow_versions(flow_info)
            else:
                self.text_area.append(f"No detailed information found for the flow: {flow_api_name}.\n")

        self.scroll_to_bottom()

    def find_flow_item_by_id(self, flow_id):
        for i in range(self.flow_tree.topLevelItemCount()):
            item = self.flow_tree.topLevelItem(i)
            checkbox = self.flow_tree.itemWidget(item, 0)
            if checkbox and flow_id in self.flow_vars and self.flow_vars[flow_id] == checkbox:
                return item
        return None

    def delete_all_versions_except_active(self):
        selected_flows = self.get_selected_flows()
        if selected_flows:
            confirmation = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete all versions except the active version for the selected flows?", QMessageBox.Yes | QMessageBox.No)
            if confirmation == QMessageBox.Yes:
                deleted_flows = []
                not_deleted_flows = []
                for flow_id in selected_flows:
                    flow_item = self.find_flow_item_by_id(flow_id)
                    if flow_item:
                        flow_api_name = flow_item.text(1)  # Assuming the DeveloperName is in the second column
                        flow_info = self.salesforce_api.retrieve_flow_definition_details(flow_api_name)
                        if flow_info:
                            active_version_id = flow_info['ActiveVersionId']
                            flow_versions = self.salesforce_api.retrieve_flow_versions(flow_info)
                            if flow_versions:
                                inactive_versions_deleted = False
                                for version in flow_versions:
                                    if version['Id'] != active_version_id:
                                        try:
                                            self.salesforce_api.delete_flow(version['Id'])
                                            inactive_versions_deleted = True
                                        except Exception as e:
                                            not_deleted_flows.append(f"{flow_api_name} (Version {version['VersionNumber']}): {str(e)}")
                                if inactive_versions_deleted:
                                    deleted_flows.append(flow_api_name)
                            else:
                                not_deleted_flows.append(f"{flow_api_name}: No versions found")
                        else:
                            not_deleted_flows.append(f"{flow_api_name}: Flow definition not found")
                    else:
                        not_deleted_flows.append(f"Flow with ID {flow_id}: Flow item not found")

                if deleted_flows:
                    self.text_area.append(f"Successfully deleted all versions except the active version for the following flows:\n{', '.join(deleted_flows)}\n")
                if not_deleted_flows:
                    self.text_area.append(f"Failed to delete versions for the following flows:\n{', '.join(not_deleted_flows)}\n")
            else:
                self.text_area.append("Deletion cancelled.\n")
        else:
            self.text_area.append("No flows selected for deletion.\n")

        self.scroll_to_bottom()

    def delete_all_versions_except_latest(self):
        selected_flows = self.get_selected_flows()
        if selected_flows:
            confirmation = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete all versions except the latest version for the selected flows?", QMessageBox.Yes | QMessageBox.No)
            if confirmation == QMessageBox.Yes:
                deleted_flows = []
                not_deleted_flows = []
                for flow_id in selected_flows:
                    flow_item = self.find_flow_item_by_id(flow_id)
                    if flow_item:
                        flow_api_name = flow_item.text(1)  # Assuming the DeveloperName is in the second column
                        flow_info = self.salesforce_api.retrieve_flow_definition_details(flow_api_name)
                        if flow_info:
                            latest_version_id = flow_info['LatestVersionId']
                            flow_versions = self.salesforce_api.retrieve_flow_versions(flow_info)
                            if flow_versions:
                                old_versions_deleted = False
                                for version in flow_versions:
                                    if version['Id'] != latest_version_id:
                                        try:
                                            self.salesforce_api.delete_flow(version['Id'])
                                            old_versions_deleted = True
                                        except Exception as e:
                                            not_deleted_flows.append(f"{flow_api_name} (Version {version['VersionNumber']}): {str(e)}")
                                if old_versions_deleted:
                                    deleted_flows.append(flow_api_name)
                            else:
                                not_deleted_flows.append(f"{flow_api_name}: No versions found")
                        else:
                            not_deleted_flows.append(f"{flow_api_name}: Flow definition not found")
                    else:
                        not_deleted_flows.append(f"Flow with ID {flow_id}: Flow item not found")

                if deleted_flows:
                    self.text_area.append(f"Successfully deleted all versions except the latest version for the following flows:\n{', '.join(deleted_flows)}\n")
                if not_deleted_flows:
                    self.text_area.append(f"Failed to delete versions for the following flows:\n{', '.join(not_deleted_flows)}\n")
            else:
                self.text_area.append("Deletion cancelled.\n")
        else:
            self.text_area.append("No flows selected for deletion.\n")

        self.scroll_to_bottom()

    def delete_entire_flowdefinition(self):
        selected_flows = self.get_selected_flows()
        if selected_flows:
            confirmation = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete all versions of the selected flows?", QMessageBox.Yes | QMessageBox.No)
            if confirmation == QMessageBox.Yes:
                deleted_flows = []
                not_deleted_flows = []
                for flow_id in selected_flows:
                    flow_info = self.salesforce_api.retrieve_flow_definition_details(flow_id)
                    if flow_info:
                        flow_versions = self.salesforce_api.retrieve_flow_versions(flow_info)
                        if flow_versions:
                            for version in flow_versions:
                                try:
                                    self.salesforce_api.delete_flow(version['Id'])
                                except Exception as e:
                                    not_deleted_flows.append(f"{flow_id} (Version {version['VersionNumber']}): {str(e)}")
                            deleted_flows.append(flow_id)
                        else:
                            not_deleted_flows.append(f"{flow_id}: No versions found")
                    else:
                        not_deleted_flows.append(f"{flow_id}: Flow definition not found")

                if deleted_flows:
                    self.text_area.append(f"Successfully deleted all versions of the following flows:\n{', '.join(deleted_flows)}\n")
                if not_deleted_flows:
                    self.text_area.append(f"Failed to delete the following flows:\n{', '.join(not_deleted_flows)}\n")
            else:
                self.text_area.append("Deletion cancelled.\n")
        else:
            self.text_area.append("No flows selected for deletion.\n")

        self.scroll_to_bottom()



    # def delete_flow(self, flow_id):
    #     delete_flow_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/Flow/{flow_id}"
    #     response = requests.delete(delete_flow_url, headers=self.headers)

    #     if response.status_code == 400 and "DELETE_FAILED" in response.text:
    #         self.text_area.append(f"Skipping deletion of active flow version with ID '{flow_id}'.\n")
    #         self.scroll_to_bottom()
    #     else:
    #         response.raise_for_status()
    #         self.text_area.append(f"Flow with ID '{flow_id}' deleted successfully.\n")
    #         self.scroll_to_bottom()

    # def delete_flowdefinition(self, flow_definition_id):
    #     delete_flowdefinition_url = f"{self.instance_url}/services/data/v52.0/tooling/sobjects/FlowDefinition/{flow_definition_id}"
    #     response = requests.delete(delete_flowdefinition_url, headers=self.headers)
    #     response.raise_for_status()
    #     self.text_area.append(f"FlowDefinition with ID '{flow_definition_id}' deleted successfully.\n")
    #     self.scroll_to_bottom()



    def save_last_config_path(self):
        config_file = os.path.join(script_dir, "last_config.txt")
        with open(config_file, "w") as file:
            file.write(self.config_path)

    def configure_app(self, config_path):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.instance_url = self.config.get('Salesforce', 'instance_url')
        self.session_id = self.config.get('Salesforce', 'session_id')
        self.headers = {'Authorization': f'Bearer {self.session_id}', 'Content-Type': 'application/json'}
        self.salesforce_api = SalesforceAPI(self.instance_url, self.headers)  # Initialize SalesforceAPI
        self.backup_manager = FlowBackupManager(self.instance_url, self.headers)  # Initialize here
        self.text_area.append(f"Loaded config file: {config_path}\n")
        self.update_connection_status()
        

    def load_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Config File", "", "INI Files (*.ini)")
        if file_path:
            self.config_path_entry.setText(file_path)
            self.config_path = file_path
            self.save_last_config_path()
            self.configure_app(file_path)  # Use unified configuration method

    def load_last_config(self):
        config_file = os.path.join(script_dir, "last_config.txt")
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                config_path = file.read().strip()
                if config_path and os.path.exists(config_path):
                    self.config_path_entry.setText(config_path)
                    self.config_path = config_path
                    self.configure_app(config_path)  # Use unified configuration method
                    

    def set_status(self, message, color="black"):
        self.status_bar.setText(message)
        self.status_bar.setStyleSheet(f"color: {color}")
        
    def update_connection_status(self):
        try:
            org_info = self.salesforce_api.get_org_info()
            is_sandbox = org_info.get('IsSandbox', False) or 'sandbox' in self.instance_url.lower()
            org_type = org_info.get('OrganizationType', 'Unknown')
            org_id = org_info.get('Id', 'Unknown')
            org_name = org_info.get('Name', 'Unknown')
            status_text = f"Connected to:  {org_name}    {org_type} Org  ({org_id}) {'(Sandbox)' if is_sandbox else '(Production)'}"
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