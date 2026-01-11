from dataclasses import dataclass
from typing import Dict, Optional, Union

from dekstop_ops import (
    create_command,
    delete_item,
    list_items,
    open_item,
    rename_item,
)

OPEN_WORDS = ("открой", "запусти", "open", "start")
RENAME_WORDS = ("переименуй", "переименовать", "rename")
DELETE_WORDS = ("удали", "удалить", "delete", "remove")
CREATE_WORDS = ("создай", "создать", "create")
EXIT_WORDS = ("выход", "exit", "quit", "q")
GET_WORDS = ("что", "какие", "get", "list")
HELP_WORDS = ("help",)

ALLOWED_KINDS = ("file", "folder")


@dataclass
class Command:
    action: str
    args: Dict[str, Union[str, bool, None]]

    def validate(self) -> Optional[str]:
        if self.action == "open" and not self.args.get("target"):
            return "Не указано, что открывать"
        if self.action == "rename" and (not self.args.get("old") or not self.args.get("new")):
            return "Недостаточно аргументов для переименования"
        if self.action == "delete" and not self.args.get("target"):
            return "Не указано, что удалять"
        if self.action == "create":
            kind = self.args.get("kind")
            if kind not in ALLOWED_KINDS:
                return "Тип должен быть file или folder"
            if kind == "file" and (not self.args.get("name") or not self.args.get("ext")):
                return "Для файла укажите имя и расширение"
            if kind == "folder" and not self.args.get("name"):
                return "Укажите имя папки"
        return None


def execute(cmd: Command) -> str:
    if cmd.action == "open":
        return open_item(cmd.args.get("target", ""))
    if cmd.action == "rename":
        return rename_item(cmd.args.get("old", ""), cmd.args.get("new", ""))
    if cmd.action == "delete":
        return delete_item(cmd.args.get("target", ""), confirm=bool(cmd.args.get("confirm", False)))
    if cmd.action == "create":
        return create_command(
            cmd.args.get("kind", ""),
            cmd.args.get("name", ""),
            cmd.args.get("ext"),
        )
    if cmd.action == "get":
        return list_items(cmd.args.get("filter"))
    if cmd.action == "help":
        return help_text()
    if cmd.action == "exit":
        return "exit"
    return "Команда не распознана"


def help_text() -> str:
    return (
        "Команды ассистента:\n"
        "- open/открой <имя> — открыть ярлык/файл\n"
        "- rename/переименуй старое -> новое — переименовать\n"
        "- delete/удали <имя> [ok] — удалить файл или папку; для непустой папки добавьте ok\n"
        "- create folder <имя> — создать папку\n"
        "- create file <имя> <расширение> — создать файл\n"
        "- get/что/какие [фильтр] — показать элементы рабочего стола\n"
        "- help — показать справку\n"
        "- exit/выход — закрыть ассистент"
    )


def parse_command(text: str) -> Union[Command, str]:
    raw = text.strip()
    if not raw:
        return "Пустая команда"

    normalized = raw.lower()
    if normalized in EXIT_WORDS:
        return Command("exit", {})

    words = normalized.split()
    raw_words = raw.split()
    if not words:
        return "Пустая команда"

    command_lower = words[0]
    command_raw = raw_words[0]

    if command_lower in HELP_WORDS:
        return Command("help", {})

    if command_lower in OPEN_WORDS:
        target = " ".join(raw_words[1:]).strip()
        return Command("open", {"target": target or None})

    if command_lower in RENAME_WORDS:
        args_raw = raw[len(command_raw):].strip()
        old_raw = None
        new_raw = None
        if "->" in args_raw:
            old_raw, new_raw = [part.strip() for part in args_raw.split("->", 1)]
        else:
            parts = args_raw.split(None, 1)
            if parts:
                old_raw = parts[0]
            if len(parts) > 1:
                new_raw = parts[1].strip()
        return Command("rename", {"old": old_raw, "new": new_raw})

    if command_lower in DELETE_WORDS:
        target_raw = raw[len(command_raw):].strip()
        confirm = False
        if target_raw.lower().endswith(" ok"):
            confirm = True
            target_raw = target_raw[:-3].rstrip()
        return Command("delete", {"target": target_raw or None, "confirm": confirm})

    if command_lower in CREATE_WORDS:
        args_raw = raw[len(command_raw):].strip()
        parts = args_raw.split()
        kind_token = parts[0].lower() if parts else None
        if kind_token in ("folder", "папка", "папку"):
            name = " ".join(parts[1:]).strip() if len(parts) > 1 else None
            return Command("create", {"kind": "folder", "name": name, "ext": None})
        if kind_token in ("file", "файл"):
            name = " ".join(parts[1:-1]).strip() if len(parts) >= 3 else None
            ext = parts[-1] if len(parts) >= 3 else None
            return Command("create", {"kind": "file", "name": name, "ext": ext})
        return Command("create", {"kind": None, "name": None, "ext": None})

    if command_lower in GET_WORDS:
        filter_raw = raw[len(command_raw):].strip()
        return Command("get", {"filter": filter_raw or None})

    return "Неверная команда. Напишите 'help' для списка команд."