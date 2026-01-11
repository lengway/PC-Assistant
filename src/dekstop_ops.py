import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, Optional
from logger import log

EXTENSION_ALLOWLIST = ("txt", "doc", "docx", "md", "json")

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
        new_path.mkdir(exist_ok=False)
        return new_path

    if kind == "file":
        if not extension:
            raise ValueError("Нужно указать расширение для файла")
        new_path = desktop / f"{name}.{extension}"
        new_path.touch(exist_ok=False)
        return new_path

    raise ValueError("Тип должен быть file или folder")


# High-level command helpers


def resolve_item(name: str) -> Optional[Path]:
    if not name:
        return None
    desktop_items = get_desktop_items()
    return desktop_items.get(name.lower())


def open_item(name: str) -> str:
    path = resolve_item(name)
    if not path:
        return "Не найдено на рабочем столе"
    if open_path(path):
        log(f"open: {path}")
        return "Открыл"
    return "Не удалось открыть"


def rename_item(old_name: str, new_name: str) -> str:
    if not old_name or not new_name:
        return "Недостаточно аргументов для переименования"
    desktop_items = get_desktop_items()
    path = desktop_items.get(old_name.lower())
    if not path:
        return "Не найдено на рабочем столе"

    new_path = path.with_name(new_name)
    if new_path.exists():
        return "Файл с таким именем уже существует"

    new_path = rename_path(path, new_name)
    log(f"rename: {path} -> {new_path}")
    return f"Переименовано в {new_path.name}"


def delete_item(name: str, confirm: bool = False) -> str:
    if not name:
        return "Не указано, что удалять"
    path = resolve_item(name)
    if not path:
        return "Не найдено на рабочем столе"

    try:
        delete_path(path, confirm=confirm)
    except (PermissionError, IsADirectoryError) as err:
        return str(err)
    log(f"delete: {path}")
    return "Удалено"


def create_command(kind: str, name: str, ext: Optional[str] = None) -> str:
    kind_l = kind.lower()
    if kind_l not in ("file", "folder"):
        return "Тип должен быть file или folder"

    if kind_l == "folder":
        if not name:
            return "Укажите имя папки"
        try:
            new_item = create_item("folder", name)
        except FileExistsError:
            return "Элемент с таким именем уже существует"
        except FileNotFoundError:
            return "Рабочий стол не найден"
        log(f"create folder: {new_item}")
        return f"Создана папка {new_item.name}"

    if not name or not ext:
        return "Для файла укажите имя и расширение"
    ext_l = ext.lower()
    if ext_l not in EXTENSION_ALLOWLIST:
        return f"Недопустимое расширение файла. Допустимые: {', '.join(EXTENSION_ALLOWLIST)}"
    try:
        new_item = create_item("file", name, ext_l)
    except FileExistsError:
        return "Элемент с таким именем уже существует"
    except FileNotFoundError:
        return "Рабочий стол не найден"
    except ValueError as err:
        return str(err)
    log(f"create file: {new_item}")
    return f"Создан файл {new_item.name}"


def list_items(filter_text: Optional[str] = None) -> str:
    desktop_items = get_desktop_items()
    if filter_text:
        key = filter_text.lower()
        item_names = sorted({item.name for k, item in desktop_items.items() if key in k})
    else:
        item_names = sorted({item.name for item in desktop_items.values()})

    if not item_names:
        return "Элементы не найдены" if filter_text else "Рабочий стол пуст"
    return "Элементы на рабочем столе:\n" + "\n".join(item_names)
        