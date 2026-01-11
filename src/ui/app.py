import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from logger import init_logger, log

LOG_PATH = None


def init(parse_and_run: Callable[[str], str]) -> None:
    global LOG_PATH
    logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    LOG_PATH = os.path.join(logs_dir, f"session-{timestamp}.log")
    init_logger(Path(LOG_PATH))
    log("Application started")
            
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Voice Assistant")
    window.setGeometry(100, 100, 300, 200)
    layout = QVBoxLayout()
    
    label = QLabel("Voice assistant for Windows\nType 'help' for instructions.")
    
    input_field = QLineEdit()
    input_field.setPlaceholderText("Enter command here...")
    
    submit_button = QPushButton("Submit")
    submit_button.clicked.connect(
        lambda: on_submit(app, window, input_field, result_label, parse_and_run)
    )
    
    result_label = QLabel("")
    
    stop_button = QPushButton("Exit")
    stop_button.clicked.connect(app.quit)
    
    layout.addWidget(label)
    layout.addWidget(input_field)
    layout.addWidget(submit_button)
    layout.addWidget(result_label)
    layout.addWidget(stop_button)
    
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())
            
def on_submit(
    app: QApplication,
    window: QWidget,
    input_field: QLineEdit,
    result_label: QLabel,
    parse_and_run: Callable[[str], str],
):
    text = input_field.text()
    try:
        result = parse_and_run(text)
    except Exception as exc:  # safeguard to keep UI alive
        log(f"Unhandled error: {exc}")
        result = "Произошла ошибка"

    if result == "exit":
        app.quit()
    else:
        result_label.setText(result)