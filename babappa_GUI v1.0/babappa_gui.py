import sys
import threading
import requests
import subprocess, os, time, socket
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QComboBox, QTextEdit, QHBoxLayout
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, pyqtSignal

API_ROOT = "http://127.0.0.1:8000"


def api_ready(host="127.0.0.1", port=8000, timeout=1):
    """Check if the API server is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def start_api_if_needed(log_cb):
    """Start the API in WSL if it's not already running."""
    if api_ready():
        log_cb("[INFO] API already running.\n")
        return True

    # Resolve install directory (PyInstaller .exe or .py file)
    appdir = os.path.dirname(
        os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)
    )
    sh_path = os.path.join(appdir, "start_babappa.sh")

    if not os.path.exists(sh_path):
        log_cb("[ERROR] start_babappa.sh missing from install directory.\n")
        return False

    log_cb("[INFO] Starting API inside WSL...\n")
    try:
        # Convert appdir to WSL path and run setup script
        cmd = [
            "wsl",
            "-d", "Ubuntu-22.04",
            "--", "bash", "-lc",
            f"cd \"$(wslpath '{appdir}')\" && bash start_babappa.sh"
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log_cb(f"[ERROR] Failed to invoke WSL: {e}\n")
        return False

    # Wait up to 60s for API to become reachable
    for _ in range(60):
        if api_ready():
            log_cb("[INFO] API is ready!\n")
            return True
        time.sleep(1)

    log_cb("[ERROR] API did not start in time. Check ~/babappa_uvicorn.log inside WSL.\n")
    return False


class BabappaGUI(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Babappa v2.0 GUI")
        self.setWindowIcon(QIcon("butterfly_icon.png"))
        self.setGeometry(400, 150, 650, 500)
        self.setStyleSheet("background-color: #707070; color: #f0f0f0;")

        self.initUI()
        self.log_signal.connect(self.safe_append_log)

        # --- Start API automatically in a background thread ---
        threading.Thread(
            target=lambda: start_api_if_needed(self.log_signal.emit),
            daemon=True
        ).start()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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

        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(["clip", "clipgard", "normal"])
        self.model_combo.setStyleSheet("background-color: #3c3c3c; color: #f0f0f0; font-weight: bold;")
        self.model_combo.setFixedWidth(120)

        # Run + Clear buttons
        btn_run = QPushButton("Run Analysis")
        btn_run.setStyleSheet("background-color: #1e9606; color: white; font-weight: bold; height: 35px;")
        btn_run.setFixedWidth(120)
        btn_run.clicked.connect(self.run_analysis)

        btn_clear = QPushButton("Clear Session")
        btn_clear.setStyleSheet("background-color: #960303; color: white; font-weight: bold; height: 35px;")
        btn_clear.setFixedWidth(120)
        btn_clear.clicked.connect(self.clear_session)

        action_layout = QHBoxLayout()
        action_layout.addStretch()
        action_layout.addWidget(QLabel("Select Model"))
        action_layout.addWidget(self.model_combo)
        action_layout.addSpacing(10)
        action_layout.addWidget(btn_run)
        action_layout.addSpacing(10)
        action_layout.addWidget(btn_clear)
        layout.addLayout(action_layout)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #f0f0f0;")
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def safe_append_log(self, text: str):
        self.log_area.append(text)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def select_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select FASTA file", "", "FASTA Files (*.fasta *.fa *.fna)"
        )
        if file_name:
            self.input_line.setText(file_name)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_line.setText(folder)

    def clear_session(self):
        self.input_line.clear()
        self.output_line.clear()
        self.model_combo.setCurrentIndex(0)
        self.log_area.clear()
        self.log_signal.emit("Session cleared. Ready for next job.\n")

    def run_analysis(self):
        input_file = self.input_line.text()
        output_dir = self.output_line.text()
        model = self.model_combo.currentText()

        if not input_file or not output_dir:
            self.log_signal.emit("Please select input file and output folder!\n")
            return

        self.log_signal.emit(f"Submitting {model} run...\n")

        def worker():
            try:
                with open(input_file, "rb") as f:
                    files = {"fasta_file": f}
                    data = {"model": model, "output_folder": output_dir}
                    resp = requests.post(f"{API_ROOT}/run", files=files, data=data, timeout=30)

                if not resp.ok:
                    self.log_signal.emit(f"Submission failed: {resp.text}\n")
                    return

                job_id = resp.json()["job_id"]
                self.log_signal.emit(f"Job submitted! Job ID: {job_id}\n")
                self.log_signal.emit("Streaming logs...\n")

                with requests.get(f"{API_ROOT}/stream/{job_id}", stream=True) as r:
                    for line in r.iter_lines(decode_unicode=True):
                        if not line or line.startswith(":"):
                            continue
                        msg = line.replace("data: ", "")
                        if msg.startswith("__status__"):
                            self.log_signal.emit(f"--- Final Status: {msg.split(':',1)[1].strip()} ---\n")
                            break
                        self.log_signal.emit(msg)

            except Exception as e:
                self.log_signal.emit(f"Error: {e}\n")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BabappaGUI()
    gui.show()
    sys.exit(app.exec())
