import os
import sys
from typing import Callable

from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

def help_text() -> str:
    return (
        "Доступные команды:\n"
        "- открыть <имя>: Открыть файл или ярлык на рабочем столе.\n"
        "- переименуй <старое имя> -> <новое имя>: Переименовать файл или папку.\n"
        "- удали <имя> [ok]: Удалить файл или папку; для непустой папки добавьте ok.\n"
        "- создай folder <имя> или создай file <имя> <расширение>: создать папку или файл на рабочем столе.\n"
        "- что / какие [фильтр]: Показать список файлов и папок на рабочем столе.\n"
        "- выход: Выйти из программы."
    )

def init(parse_and_run: Callable[[str], str]) -> None:
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Voice Assistant")
    window.setGeometry(100, 100, 300, 200)
    layout = QVBoxLayout()
    
    label = QLabel("Voice assistant for Windows\nType 'help' for instructions.")
    
    input_field = QLineEdit()
    input_field.setPlaceholderText("Enter command here...")
    submit_button = QPushButton("Submit")
    result_label = QLabel("")
    submit_button.clicked.connect(
        lambda: on_submit(app, window, input_field, result_label, parse_and_run)
    )
    
    layout.addWidget(label)
    layout.addWidget(input_field)
    layout.addWidget(submit_button)
    layout.addWidget(result_label)
    
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())
    
    if not os.path.exists("logs/log.txt"):
        with open("logs/log.txt", "w") as f:
            f.write("Application started\n")
            
def on_submit(
    app: QApplication,
    window: QWidget,
    input_field: QLineEdit,
    result_label: QLabel,
    parse_and_run: Callable[[str], str],
):
    text = input_field.text()
    result = parse_and_run(text)
    if result == "exit":
        app.quit()
    else:
        result_label.setText(result)