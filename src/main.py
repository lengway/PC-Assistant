import sys
from ui.app import init
from asr import transcribe_once
from core.desktop import Command, execute, help_text, parse_command
from llm_parser import parse_with_llm
from pipeline import coerce_steps, run_plan


def parse_and_run(text: str) -> str:
    plan = parse_with_llm(text)
    if isinstance(plan, str):
        # error string from parser
        return plan
    commands = coerce_steps(plan)
    return run_plan(commands)

def main() -> None:
    init(parse_and_run)


if __name__ == "__main__":
    if sys.platform != "win32":
        print("Предупреждение: код рассчитан на Windows")
    main()
