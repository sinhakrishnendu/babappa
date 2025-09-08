import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QComboBox, QTextEdit, QHBoxLayout
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt
import requests

API_URL = "http://127.0.0.1:8000/run"  # Fixed to match your FastAPI endpoint

class BabappaGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Babappa v2.0 GUI")
        self.setWindowIcon(QIcon("butterfly_icon.png"))
        self.setGeometry(400, 150, 650, 500)
        self.setStyleSheet("background-color: #2e2e2e; color: #f0f0f0;")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Title
        title = QLabel("Babappa v2.0")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Input file
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Select input FASTA file")
        self.input_line.setReadOnly(True)
        self.input_line.setStyleSheet("background-color: #3c3c3c; color: #f0f0f0;")

        btn_input = QPushButton("Browse")
        btn_input.setStyleSheet("background-color: #9c7503; color: white; font-weight: bold;")
        btn_input.setFixedWidth(80)
        btn_input.clicked.connect(self.select_input_file)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(btn_input)
        layout.addLayout(input_layout)

        # Output folder
        self.output_line = QLineEdit()
        self.output_line.setPlaceholderText("Select output folder")
        self.output_line.setReadOnly(True)
        self.output_line.setStyleSheet("background-color: #3c3c3c; color: #f0f0f0;")

        btn_output = QPushButton("Browse")
        btn_output.setStyleSheet("background-color: #9c7503; color: white; font-weight: bold;")
        btn_output.setFixedWidth(80)
        btn_output.clicked.connect(self.select_output_folder)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_line)
        output_layout.addWidget(btn_output)
        layout.addLayout(output_layout)

        # Model selection dropdown
        self.model_combo = QComboBox()
        self.model_combo.addItems(["clip", "clipgard", "normal"])
        self.model_combo.setStyleSheet("background-color: #3c3c3c; color: #f0f0f0; font-weight: bold;")
        self.model_combo.setFixedWidth(120)

        # Run button
        btn_run = QPushButton("Run Analysis")
        btn_run.setStyleSheet(
            "background-color: #4caf50; color: white; font-weight: bold; height: 35px;"
        )
        btn_run.setFixedWidth(120)
        btn_run.clicked.connect(self.run_analysis)  # Now works

        # Layout for model + run button in one line
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        action_layout.addWidget(QLabel("Select Model"))
        action_layout.addWidget(self.model_combo)
        action_layout.addSpacing(10)
        action_layout.addWidget(btn_run)
        layout.addLayout(action_layout)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #f0f0f0;")
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def select_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select FASTA file", "", "FASTA Files (*.fasta *.fa *.fna)")
        if file_name:
            self.input_line.setText(file_name)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_line.setText(folder)

    # <--- run_analysis must be inside the class
    def run_analysis(self):
        input_file = self.input_line.text()
        output_dir = self.output_line.text()
        model = self.model_combo.currentText()

        if not input_file or not output_dir:
            self.log_area.append("Please select input file and output folder!")
            return

        self.log_area.append(f"Submitting {model} run...\n")

        import threading

        def worker():
            try:
                with open(input_file, "rb") as f:
                    files = {"fasta_file": f}
                    data = {"model": model, "output_folder": output_dir}
                    response = requests.post(API_URL, files=files, data=data)

                if response.ok:
                    job_id = response.json()["job_id"]
                    self.log_area.append(f"Job submitted! Job ID: {job_id}\n")
                    self.log_area.append("Fetching logs...\n")

                    stream_url = f"http://127.0.0.1:8000/stream/{job_id}"
                    with requests.get(stream_url, stream=True) as r:
                        for line in r.iter_lines(decode_unicode=True):
                            if line:
                                log_line = line.replace("data: ", "")
                                self.log_area.append(log_line)
                                self.log_area.verticalScrollBar().setValue(
                                    self.log_area.verticalScrollBar().maximum()
                                )

                    status_url = f"http://127.0.0.1:8000/status/{job_id}"
                    status_resp = requests.get(status_url).json()
                    self.log_area.append(f"\nRun finished with status: {status_resp['status']}\n")
                else:
                    self.log_area.append(f"Submission failed: {response.text}\n")

            except Exception as e:
                self.log_area.append(f"Error: {e}\n")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BabappaGUI()
    gui.show()
    sys.exit(app.exec())
