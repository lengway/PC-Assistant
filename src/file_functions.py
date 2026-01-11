import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Desktop discovery


def candidate_desktops() -> Iterable[Path]:
    """Yield desktop folders: user Desktop/"Рабочий стол" and Public Desktop."""
    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    public_root = Path(os.environ.get("PUBLIC", r"C:\\Users\\Public"))
    desktop_names = ("Desktop", "Рабочий стол")

    seen = set()
    for base in (user_profile, public_root):
        for name in desktop_names:
            desk = (base / name).resolve()
            if desk.exists() and desk not in seen:
                seen.add(desk)
                yield desk


def first_desktop() -> Optional[Path]:
    """Return the first existing desktop path or None."""
    return next(candidate_desktops(), None)


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


# File operations


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


def delete_path(path: Path, confirm: bool = False) -> None:
    """Delete files; delete directories recursively only if confirmed."""
    if path.is_dir():
        has_children = any(path.iterdir())
        if has_children and not confirm:
            raise PermissionError("Папка не пуста, добавьте 'ok' после имени для удаления")
        if confirm:
            shutil.rmtree(path)
        else:
            path.rmdir()
        return

    path.unlink()


def create_item(kind: str, name: str, extension: Optional[str] = None) -> Path:
    """Create a folder or file on the desktop."""
    desktop = first_desktop()
    if not desktop:
        raise FileNotFoundError("Desktop not found")

    if kind == "folder":
        new_path = desktop / name
        new_path.mkdir(exist_ok=True)
        return new_path

    if kind == "file":
        if not extension:
            raise ValueError("Нужно указать расширение для файла")
        new_path = desktop / f"{name}.{extension}"
        new_path.touch(exist_ok=True)
        return new_path

    raise ValueError("Тип должен быть file или folder")


# Command handlers (raw command parsing per operation)


def handle_open(raw_words: List[str], raw: str) -> str:
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


def handle_rename(raw: str, command_raw: str) -> str:
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


def handle_delete(raw: str, command_raw: str) -> str:
    target_raw = raw[len(command_raw):].strip()
    confirm = False
    if target_raw.lower().endswith(" ok"):
        confirm = True
        target_raw = target_raw[:-3].rstrip()

    target_key = target_raw.lower()
    if not target_key:
        return "Не указано, что удалять"

    desktop_items = get_desktop_items()
    path = desktop_items.get(target_key)
    if not path:
        return "Не найдено на рабочем столе"

    try:
        delete_path(path, confirm=confirm)
    except (PermissionError, IsADirectoryError) as err:
        return str(err)
    return "Удалено"


def handle_create(raw: str, command_raw: str) -> str:
    args_raw = raw[len(command_raw):].strip()
    parts = args_raw.split()
    if len(parts) < 2:
        return "Формат: create file <имя> <расширение> или create folder <имя>"

    kind = parts[0].lower()
    if kind in ("folder", "папку", "папка"):
        name = " ".join(parts[1:]).strip()
        if not name:
            return "Укажите имя папки"
        try:
            new_item = create_item("folder", name)
        except FileNotFoundError:
            return "Рабочий стол не найден"
        return f"Создана папка {new_item.name}"

    if kind in ("file", "файл"):
        if len(parts) < 3:
            return "Для файла укажите имя и расширение"
        name = " ".join(parts[1:-1]).strip()
        ext = parts[-1]
        if not name or not ext:
            return "Для файла укажите имя и расширение"
        try:
            new_item = create_item("file", name, ext)
        except FileNotFoundError:
            return "Рабочий стол не найден"
        except ValueError as err:
            return str(err)
        return f"Создан файл {new_item.name}"

    return "Тип должен быть file или folder"


def handle_get(raw: str, command_raw: str) -> str:
    desktop_items = get_desktop_items()
    target_raw = raw[len(command_raw):].strip()

    if target_raw:
        target_key = target_raw.lower()
        item_names = sorted(
            item.name for key, item in desktop_items.items() if target_key in key
        )
        return (
            "Элементы на рабочем столе:\n" + "\n".join(item_names)
            if item_names
            else "Элементы не найдены"
        )

    if not desktop_items:
        return "Рабочий стол пуст"
    item_names = sorted(item.name for item in desktop_items.values())
    return "Элементы на рабочем столе:\n" + "\n".join(item_names)