import sys
import requests
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QStackedLayout, QFrame, QTextEdit, QDialog, QScrollArea, QCheckBox, QMessageBox, QFileDialog, QSpinBox, QComboBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QTextCursor
import html
import json
from trackers import KNOWN_TRACKERS  # Import the KNOWN_TRACKERS dictionary

def scan_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")
        trackers_found = []

        for tag in soup.find_all(["script", "iframe", "img"]):
            src = tag.get("src") or tag.get("data-src")
            if src:
                for keyword, (category, company) in KNOWN_TRACKERS.items():
                    if keyword in src:
                        trackers_found.append({
                            "name": keyword,
                            "category": category,
                            "company": company,
                            "url": src
                        })
                        break

        return trackers_found, soup.prettify()
    except Exception as e:
        print(f"Scan failed: {e}")
        return [], ""

class DetailedReportDialog(QDialog):
    def __init__(self, html_content, trackers):
        super().__init__()
        self.setWindowTitle("Detailed Tracker Report")
        self.setMinimumSize(800, 600)

        self.original_html = html_content
        self.trackers = trackers

        self.layout = QVBoxLayout(self)
        self.filter_checkbox = QCheckBox("Show only tracker code")
        self.filter_checkbox.stateChanged.connect(self.update_view)
        self.layout.addWidget(self.filter_checkbox)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.viewport().installEventFilter(self)

        self.scroll.setWidget(self.report_view)
        self.layout.addWidget(self.scroll)
        self.setLayout(self.layout)
        self.update_view()

    def update_view(self):
        escaped_html = html.escape(self.original_html)
        if self.filter_checkbox.isChecked():
            lines = escaped_html.split('\n')
            tracker_lines = [line for line in lines if any(html.escape(t['name']) in line for t in self.trackers)]
            escaped_html = '\n'.join(tracker_lines)

        for tracker in self.trackers:
            name = html.escape(tracker["name"])
            highlight = f'<a href="#" style="text-decoration:none; background-color: yellow; border: 1px dashed orange; color: black;" title="Click for tracker info">{name}</a>'
            escaped_html = escaped_html.replace(name, highlight)

        self.report_view.setHtml(f"<pre style='font-family: monospace;'>{escaped_html}</pre>")

    def eventFilter(self, source, event):
        if event.type() == event.Type.MouseButtonPress:
            cursor = self.report_view.cursorForPosition(event.position().toPoint())
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText()
            if word in KNOWN_TRACKERS:
                category, company = KNOWN_TRACKERS[word]
                QMessageBox.information(self, "Tracker Info",
                    f"Tracker: {word}\nCategory: {category}\nCompany: {company}")
        return super().eventFilter(source, event)

class ChatWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat")
        self.setGeometry(200, 200, 400, 300)

        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message...")
        self.chat_send_button = QPushButton("Send")
        self.chat_send_button.clicked.connect(self.send_message)

        self.chat_layout = QVBoxLayout()
        self.chat_layout.addWidget(self.chat_box)
        self.chat_layout.addWidget(self.chat_input)
        self.chat_layout.addWidget(self.chat_send_button)

        self.setLayout(self.chat_layout)

    def send_message(self):
        message = self.chat_input.text().strip()
        if message:
            self.chat_box.append(f"You: {message}")
            response = self.get_chat_response(message)
            self.chat_box.append(f"Bot: {response}")
            self.chat_input.clear()

    def get_chat_response(self, message):
        # Rule-based responses
        message = message.lower()
        if "hello" in message or "hi" in message:
            return "Hello! How can I assist you today?"
        elif "scan" in message:
            return "To scan a website, please go to the dashboard and enter the URL."
        elif "report" in message:
            return "You can view previous scan reports in the Reports section."
        elif "settings" in message:
            return "You can change the settings in the Settings section."
        elif "export" in message:
            return "You can export the reports by clicking the Export Reports button in the Reports section."
        else:
            return "I'm sorry, I didn't understand that. Can you please rephrase?"

class PrivacyLensApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Privacy Lens")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(self.light_theme())

        self.scan_history = []

        self.main_layout = QHBoxLayout(self)
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(80)
        self.sidebar.setStyleSheet("background-color: #1f2532; border-radius: 8px;")
        self.sidebar.setLayout(self.sidebar_layout)

        self.home_btn = QPushButton()
        self.home_btn.setIcon(QIcon("icons/Home.svg"))
        self.home_btn.setFixedSize(60, 60)
        self.home_btn.setStyleSheet("QPushButton { border: none; background: none; } QPushButton:hover { background-color: #2e3a4d; border-radius: 10px; }")
        self.home_btn.clicked.connect(self.show_dashboard)

        self.reports_btn = QPushButton()
        self.reports_btn.setIcon(QIcon("icons/Analytics.svg"))
        self.reports_btn.setFixedSize(60, 60)
        self.reports_btn.setStyleSheet(self.home_btn.styleSheet())
        self.reports_btn.clicked.connect(self.show_reports)

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon("icons/Settings.svg"))
        self.settings_btn.setFixedSize(60, 60)
        self.settings_btn.setStyleSheet(self.home_btn.styleSheet())
        self.settings_btn.clicked.connect(self.show_settings)

        self.chat_btn = QPushButton()
        self.chat_btn.setIcon(QIcon("icons/Chat.svg"))
        self.chat_btn.setFixedSize(60, 60)
        self.chat_btn.setStyleSheet(self.home_btn.styleSheet())
        self.chat_btn.clicked.connect(self.open_chat)

        self.sidebar_layout.addWidget(self.home_btn)
        self.sidebar_layout.addWidget(self.reports_btn)
        self.sidebar_layout.addWidget(self.settings_btn)
        self.sidebar_layout.addWidget(self.chat_btn)

        self.stack = QStackedLayout()

        self.dashboard_widget = QWidget()
        self.dashboard_layout = QVBoxLayout(self.dashboard_widget)
        self.dashboard_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_label = QLabel("Privacy Lens")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1f2532;")
        self.dashboard_layout.addWidget(self.title_label)

        self.search_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter website URL...")
        self.url_input.setStyleSheet("padding: 8px; font-size: 14px; border: 2px solid #ccc; border-radius: 5px;")

        self.scan_button = QPushButton("Scan")
        self.scan_button.setStyleSheet("padding: 8px; background-color: #3f51b5; color: white; border-radius: 5px;")
        self.scan_button.clicked.connect(self.perform_scan)

        self.search_layout.addWidget(self.url_input)
        self.search_layout.addWidget(self.scan_button)
        self.dashboard_layout.addLayout(self.search_layout)

        self.tracker_table = QTableWidget()
        self.tracker_table.setColumnCount(4)
        self.tracker_table.setHorizontalHeaderLabels(["URL", "Privacy Score", "Trackers", "Report"])
        self.tracker_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.dashboard_layout.addWidget(self.tracker_table)

        # Add Chat Button to Dashboard
        self.chat_open_button = QPushButton("Chat")
        self.chat_open_button.setStyleSheet("padding: 8px; background-color: #3f51b5; color: white; border-radius: 5px;")
        self.chat_open_button.clicked.connect(self.open_chat)
        self.dashboard_layout.addWidget(self.chat_open_button, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        self.reports_widget = QWidget()
        self.reports_layout = QVBoxLayout(self.reports_widget)
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(4)
        self.reports_table.setHorizontalHeaderLabels(["URL", "Privacy Score", "Trackers", "Report"])
        self.reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.reports_layout.addWidget(QLabel("Previous Scan Reports"))
        self.reports_layout.addWidget(self.reports_table)

        # Add Export Button
        self.export_button = QPushButton("Export Reports")
        self.export_button.setStyleSheet("padding: 8px; background-color: #3f51b5; color: white; border-radius: 5px;")
        self.export_button.clicked.connect(self.export_reports)
        self.reports_layout.addWidget(self.export_button)

        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_widget)
        self.settings_layout.addWidget(QLabel("Settings"))

        # Add settings options
        self.notifications_checkbox = QCheckBox("Enable Notifications")
        self.scan_interval_spinbox = QSpinBox()
        self.scan_interval_spinbox.setRange(1, 60)
        self.scan_interval_spinbox.setValue(10)
        self.theme_combobox = QComboBox()
        self.theme_combobox.addItems(["Light", "Dark"])
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(["English", "Spanish", "French", "German", "Chinese"])

        # Group settings
        general_settings_group = QGroupBox("General Settings")
        general_settings_layout = QFormLayout()
        general_settings_layout.addRow(QLabel("Enable Notifications:"), self.notifications_checkbox)
        general_settings_layout.addRow(QLabel("Scan Interval (minutes):"), self.scan_interval_spinbox)
        general_settings_group.setLayout(general_settings_layout)

        appearance_settings_group = QGroupBox("Appearance Settings")
        appearance_settings_layout = QFormLayout()
        appearance_settings_layout.addRow(QLabel("Theme:"), self.theme_combobox)
        appearance_settings_layout.addRow(QLabel("Language:"), self.language_combobox)
        appearance_settings_group.setLayout(appearance_settings_layout)

        self.settings_layout.addWidget(general_settings_group)
        self.settings_layout.addWidget(appearance_settings_group)

        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.setStyleSheet("padding: 8px; background-color: #3f51b5; color: white; border-radius: 5px;")
        self.save_settings_button.clicked.connect(self.save_settings)
        self.settings_layout.addWidget(self.save_settings_button)

        self.stack.addWidget(self.dashboard_widget)
        self.stack.addWidget(self.reports_widget)
        self.stack.addWidget(self.settings_widget)

        self.main_layout.addWidget(self.sidebar)
        container = QWidget()
        container.setLayout(self.stack)
        self.main_layout.addWidget(container)

        self.setLayout(self.main_layout)

    def show_dashboard(self):
        self.stack.setCurrentWidget(self.dashboard_widget)

    def show_reports(self):
        self.stack.setCurrentWidget(self.reports_widget)
        self.populate_reports_table()

    def show_settings(self):
        self.stack.setCurrentWidget(self.settings_widget)

    def open_chat(self):
        self.chat_window = ChatWindow()
        self.chat_window.exec()

    def perform_scan(self):
        url = self.url_input.text().strip()
        if not url.startswith("http"):
            url = "http://" + url
        trackers, html = scan_url(url)
        score = max(0, 100 - (len(trackers) * 3))

        result = {"url": url, "score": score, "trackers": trackers, "html": html}
        self.scan_history.append(result)

        self.tracker_table.setRowCount(1)
        self.tracker_table.setItem(0, 0, QTableWidgetItem(url))
        self.tracker_table.setItem(0, 1, QTableWidgetItem(f"{score}%"))
        self.tracker_table.setItem(0, 2, QTableWidgetItem(str(len(trackers))))
        view_btn = QPushButton("View Report")
        view_btn.clicked.connect(lambda: self.show_detailed_report(html, trackers))
        self.tracker_table.setCellWidget(0, 3, view_btn)

    def populate_reports_table(self):
        self.reports_table.setRowCount(len(self.scan_history))
        for i, scan in enumerate(self.scan_history):
            self.reports_table.setItem(i, 0, QTableWidgetItem(scan["url"]))
            self.reports_table.setItem(i, 1, QTableWidgetItem(f"{scan['score']}%"))
            self.reports_table.setItem(i, 2, QTableWidgetItem(str(len(scan["trackers"]))))
            btn = QPushButton("View Report")
            btn.clicked.connect(lambda _, h=scan["html"], t=scan["trackers"]: self.show_detailed_report(h, t))
            self.reports_table.setCellWidget(i, 3, btn)

    def show_detailed_report(self, html, trackers):
        dialog = DetailedReportDialog(html, trackers)
        dialog.exec()

    def export_reports(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Reports", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    json.dump(self.scan_history, file, indent=4)
                QMessageBox.information(self, "Export Successful", "Reports have been successfully exported.")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting reports: {e}")

    def save_settings(self):
        notifications_enabled = self.notifications_checkbox.isChecked()
        scan_interval = self.scan_interval_spinbox.value()
        theme = self.theme_combobox.currentText()
        language = self.language_combobox.currentText()
        # Apply theme
        if theme == "Dark":
            self.setStyleSheet(self.dark_theme())
        else:
            self.setStyleSheet(self.light_theme())
        # Save settings logic here
        QMessageBox.information(self, "Settings Saved", f"Notifications: {'Enabled' if notifications_enabled else 'Disabled'}\nScan Interval: {scan_interval} minutes\nTheme: {theme}\nLanguage: {language}")

    def light_theme(self):
        return """
        QWidget {
            background-color: #f0f2f5;
            color: #000;
        }
        QLineEdit, QSpinBox, QComboBox, QTextEdit {
            background-color: #fff;
            color: #000;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        QPushButton {
            background-color: #3f51b5;
            color: white;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #2e3a4d;
        }
        QTableWidget {
            background-color: #fff;
            color: #000;
            border: 1px solid #ccc;
        }
        QHeaderView::section {
            background-color: #3f51b5;
            color: white;
        }
        """

    def dark_theme(self):
        return """
        QWidget {
            background-color: #2e3a4d;
            color: #fff;
        }
        QLineEdit, QSpinBox, QComboBox, QTextEdit {
            background-color: #3e4a5e;
            color: #fff;
            border: 1px solid #555;
            border-radius: 5px;
        }
        QPushButton {
            background-color: #3f51b5;
            color: white;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #2e3a4d;
        }
        QTableWidget {
            background-color: #3e4a5e;
            color: #fff;
            border: 1px solid #555;
        }
        QHeaderView::section {
            background-color: #3f51b5;
            color: white;
        }
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PrivacyLensApp()
    window.show()
    sys.exit(app.exec())