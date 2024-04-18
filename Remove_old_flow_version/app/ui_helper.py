# ui_helper.py
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QCheckBox, QTextEdit, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
import os

class UIHelper:
    def __init__(self, flow_tree, flow_vars, text_area):
        self.flow_tree = flow_tree
        self.flow_vars = flow_vars
        self.text_area = text_area


    # ui_helper.py
    def create_flow_checkboxes(self, all_flows):
        self.flow_tree.clear()
        self.flow_vars.clear()

        for flow in all_flows:
            if flow is None:
                print("Warning: Skipped processing a None entry in all_flows")
                continue  # Skip processing if the flow entry is None

            try:
                flow_id = str(flow["Id"])
                flow_item = QTreeWidgetItem(self.flow_tree)
                flow_item.setText(1, flow["DeveloperName"])
                flow_item.setText(4, flow["LastModifiedDate"].split('T')[0])

                latest_version_number = int(flow["LatestVersion"]["VersionNumber"])
                flow_item.setText(2, str(latest_version_number).zfill(3))
                flow_item.setData(2, Qt.UserRole, latest_version_number)

                # Retrieve the ActiveVersion number; handle if ActiveVersion is None
                active_version = flow.get("ActiveVersion")
                active_version_number = None if active_version is None else active_version.get("VersionNumber")
                flow_item.setText(3, str(active_version_number).zfill(3) if active_version_number else "")

                latest_version_id = flow["LatestVersionId"]
                active_version_id = flow.get("ActiveVersionId")
                
                # Determine if the flow is active
                is_active = latest_version_id == active_version_id if active_version_id else False
                flow_item.setText(5, "Yes" if is_active else "No")

                # Update the font if the flow is active
                if is_active:
                    font = flow_item.font(5)
                    font.setBold(True)
                    flow_item.setFont(5, font)

                # Create a checkbox regardless of active status
                checkbox = QCheckBox()
                self.flow_vars[flow_id] = checkbox
                self.flow_tree.setItemWidget(flow_item, 0, checkbox)

            except Exception as e:
                print(f"Error processing flow {flow}: {e}")
                # Even in case of an error, ensure a checkbox is created for consistency
                checkbox = QCheckBox()
                checkbox.setDisabled(True)  # Optionally disable the checkbox if there is an error
                self.flow_vars[flow_id] = checkbox
                self.flow_tree.setItemWidget(flow_item, 0, checkbox)

        self.flow_tree.setSortingEnabled(True)
        self.flow_tree.sortByColumn(2, Qt.AscendingOrder)
        self.flow_tree.expandAll()

        return self.flow_vars



    def update_flow_checkboxes(self, all_flows):
        for flow in all_flows:
            flow_id = str(flow['Id'])
            checkbox = self.flow_vars.get(flow_id)
            if checkbox:
                item = self.flow_tree.findItems(flow["DeveloperName"], Qt.MatchExactly, 1)[0]
                self.flow_tree.setItemWidget(item, 0, checkbox)

    def find_flow_item_by_id(self, flow_id):
        for i in range(self.flow_tree.topLevelItemCount()):
            item = self.flow_tree.topLevelItem(i)
            checkbox = self.flow_tree.itemWidget(item, 0)
            if checkbox and flow_id in self.flow_vars and self.flow_vars[flow_id] == checkbox:
                return item.text(1)
        return None

    def scroll_to_bottom(self):
        cursor = self.text_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_area.setTextCursor(cursor)

    def save_last_config_path(self, config_path):
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "last_config.txt")
        with open(config_file, "w") as file:
            file.write(config_path)

    def load_last_config_path(self):
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "last_config.txt")
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                config_path = file.read().strip()
                if config_path and os.path.exists(config_path):
                    return config_path
        return None

    def select_config_file(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Config File", "", "INI Files (*.ini)")
        return file_path
    
    
    def append_text(self, text):
        self.text_area.append(text)