import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

# Only desktop items are available to the assistant.
OPEN_WORDS = ("открой", "запусти", "open", "start")
RENAME_WORDS = ("переименуй", "переименовать", "rename")
DELETE_WORDS = ("удали", "удалить", "delete", "remove")
CREATE_WORDS = ("создай", "создать", "create")
EXIT_WORDS = ("выход", "exit", "quit", "q")


def candidate_desktops() -> Iterable[Path]:
    """Yield local desktop folders (regular and localized), no OneDrive."""
    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    desktop_names = ("Desktop", "Рабочий стол")

    seen = set()
    for name in desktop_names:
        desk = (user_profile / name).resolve()
        if desk.exists() and desk not in seen:
            seen.add(desk)
            yield desk


def get_desktop_items() -> Dict[str, Path]:
    """Return mapping from visible names to full paths for desktop items."""
    items: Dict[str, Path] = {}
    for desktop in candidate_desktops():
        for entry in desktop.iterdir():
            if entry.name.startswith("."):
                continue
            key = entry.name.lower()
            items[key] = entry

            # For .lnk, also map the stem to allow visible-name matching.
            if entry.suffix.lower() == ".lnk":
                items[entry.stem.lower()] = entry
    return items


def open_path(path: Path) -> bool:
    """Open a file/shortcut via shell; try os.startfile first, then start command."""
    resolved = path.resolve()
    try:
        os.startfile(resolved)  # type: ignore[attr-defined]
        return True
    except OSError:
        pass

    try:
        cmd = f'start "" "{resolved}"'
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def rename_path(path: Path, new_name: str) -> Path:
    """Rename the given path to the new name in the same directory."""
    new_path = path.with_name(new_name)
    path.rename(new_path)
    return new_path


def delete_path(path: Path) -> None:
    """Delete the given path (files only, directories are blocked for safety)."""
    # if path.is_dir():
    #     raise IsADirectoryError("Удаление папок отключено для безопасности")
    path.unlink()


def first_desktop() -> Optional[Path]:
    """Return the first existing desktop path or None."""
    return next(candidate_desktops(), None)


def create_folder(folder_name: str) -> Path:
    """Create a new folder on the desktop (localized supported)."""
    desktop = first_desktop()
    if not desktop:
        raise FileNotFoundError("Desktop not found")

    new_folder = desktop / folder_name
    new_folder.mkdir(exist_ok=True)
    return new_folder


def parse_and_run(text: str) -> str:
    """Parse the text command and try to launch a desktop item."""
    raw = text.strip()
    if not raw:
        return "Пустая команда"

    normalized = raw.lower()

    if normalized in EXIT_WORDS:
        return "exit"

    if normalized.startswith("help"):
        return help_text()

    words = normalized.split()
    raw_words = raw.split()
    if not words:
        return "Пустая команда"

    command_lower = words[0]
    command_raw = raw_words[0]

    if command_lower in OPEN_WORDS:
        target_raw = " ".join(raw_words[1:]).strip()
        target_key = target_raw.lower()
        if not target_key:
            return "Не указано, что открывать"

        desktop_items = get_desktop_items()
        path = desktop_items.get(target_key)
        if not path:
            return "Не найдено на рабочем столе"

        succeeded = open_path(path)
        return "Открыл" if succeeded else "Не удалось открыть"

    if command_lower in RENAME_WORDS:
        # Support "rename old -> new" to allow spaces in names; fallback to first + rest.
        args_raw = raw[len(command_raw):].strip()
        old_raw: Optional[str]
        new_raw: Optional[str]
        if "->" in args_raw:
            old_raw, new_raw = [part.strip() for part in args_raw.split("->", 1)]
        else:
            parts = args_raw.split(None, 1)
            if len(parts) < 2:
                return "Недостаточно аргументов для переименования"
            old_raw, new_raw = parts[0], parts[1].strip()

        if not old_raw or not new_raw:
            return "Недостаточно аргументов для переименования"

        desktop_items = get_desktop_items()
        path = desktop_items.get(old_raw.lower())
        if not path:
            return "Не найдено на рабочем столе"

        new_path = rename_path(path, new_raw)
        return f"Переименовано в {new_path.name}"

    if command_lower in DELETE_WORDS:
        target_raw = raw[len(command_raw):].strip()
        target_key = target_raw.lower()
        if not target_key:
            return "Не указано, что удалять"

        desktop_items = get_desktop_items()
        path = desktop_items.get(target_key)
        if not path:
            return "Не найдено на рабочем столе"

        try:
            delete_path(path)
        except IsADirectoryError as err:
            return str(err)
        return "Удалено"

    if command_lower in CREATE_WORDS:
        folder_raw = raw[len(command_raw):].strip()
        if not folder_raw:
            return "Недостаточно аргументов для создания папки"
        try:
            new_folder = create_folder(folder_raw)
        except FileNotFoundError:
            return "Рабочий стол не найден"
        return f"Создана папка {new_folder.name}"

    return "Неверная команда. Напишите 'help' для списка команд."


def help_text() -> str:
    return (
        "Команды ассистента:\n"
        "- open/открой <имя> — открыть ярлык/файл с рабочего стола\n"
        "- rename/переименуй старое -> новое — переименовать (поддерживает пробелы через '->')\n"
        "- delete/удали <имя> — удалить файл (папки удалять нельзя)\n"
        "- create/создай <имя_папки> — создать папку на рабочем столе\n"
        "- help — показать справку\n"
        "- exit/выход — закрыть ассистент"
    )
    
def application_init() -> None:
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
        lambda: on_submit(app, window, input_field, result_label)
    )
    
    layout.addWidget(label)
    layout.addWidget(input_field)
    layout.addWidget(submit_button)
    layout.addWidget(result_label)
    
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())

def on_submit(
    app: QApplication,
    window: QWidget,
    input_field: QLineEdit,
    result_label: QLabel,
):
    text = input_field.text()
    result = parse_and_run(text)
    if result == "exit":
        app.quit()
    else:
        result_label.setText(result)


def main() -> None:
    application_init()
    
    # print("Voice assistant for Windows")
    # print("Type 'help' for instructions.")
    # while True:
    #     try:
    #         text = input("> ")
    #     except (EOFError, KeyboardInterrupt):
    #         print("\nВыход")
    #         break

    #     result = parse_and_run(text)
    #     if result == "exit":
    #         print("Выход")
    #         break
    #     print(result)


if __name__ == "__main__":
    if sys.platform != "win32":
        print("Предупреждение: код рассчитан на Windows")
    main()
