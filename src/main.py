import sys
from app_initialization import init
from file_functions import (
    handle_create,
    handle_delete,
    handle_get,
    handle_open,
    handle_rename,
)

# Only desktop items are available to the assistant.
OPEN_WORDS = ("открой", "запусти", "open", "start")
RENAME_WORDS = ("переименуй", "переименовать", "rename")
DELETE_WORDS = ("удали", "удалить", "delete", "remove")
CREATE_WORDS = ("создай", "создать", "create")
EXIT_WORDS = ("выход", "exit", "quit", "q")
GET_WORDS = ("что", "какие", "get", "list")


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
        return handle_open(raw_words, raw)

    if command_lower in RENAME_WORDS:
        return handle_rename(raw, command_raw)

    if command_lower in DELETE_WORDS:
        return handle_delete(raw, command_raw)

    if command_lower in CREATE_WORDS:
        return handle_create(raw, command_raw)
    
    if command_lower in GET_WORDS:
        return handle_get(raw, command_raw)
    

    return "Неверная команда. Напишите 'help' для списка команд."

def help_text() -> str:
    return (
        "Команды ассистента:\n"
        "- open/открой <имя> — открыть ярлык/файл с рабочего стола\n"
        "- rename/переименуй старое -> новое — переименовать (поддерживает пробелы через '->')\n"
        "- delete/удали <имя> [ok] — удалить файл или папку; для непустой папки добавьте ok\n"
        "- create/создай folder <имя> — создать папку на рабочем столе\n"
        "- create/создай file <имя> <расширение> — создать файл на рабочем столе\n"
        "- get/что/какие [фильтр] — показать элементы рабочего стола (опционально по подстроке)\n"
        "- help — показать справку\n"
        "- exit/выход — закрыть ассистент"
    )
    

def main() -> None:
    init(parse_and_run)


if __name__ == "__main__":
    if sys.platform != "win32":
        print("Предупреждение: код рассчитан на Windows")
    main()
