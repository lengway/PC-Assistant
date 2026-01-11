import sys
from ui.app import init
from core.desktop import Command, execute, help_text, parse_command


def parse_and_run(text: str) -> str:
    parsed = parse_command(text)
    if isinstance(parsed, str):
        return parsed
    assert isinstance(parsed, Command)
    validation_error = parsed.validate()
    if validation_error:
        return validation_error
    return execute(parsed)

def main() -> None:
    init(parse_and_run)


if __name__ == "__main__":
    if sys.platform != "win32":
        print("Предупреждение: код рассчитан на Windows")
    main()
