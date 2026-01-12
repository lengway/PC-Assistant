from typing import List, Union

from core.desktop import Command, execute


def run_plan(steps: List[Command]) -> str:
    """Validate and execute a list of commands, returning combined output."""
    results: List[str] = []
    for step in steps:
        error = step.validate()
        if error:
            results.append(error)
            break
        results.append(execute(step))
    return "\n".join(results)


def command_from_dict(step: dict) -> Command:
    return Command(step.get("action", ""), step.get("args", {}))


def coerce_steps(steps: List[Union[Command, dict, str]]) -> List[Command]:
    prepared: List[Command] = []
    for step in steps:
        if isinstance(step, Command):
            prepared.append(step)
        elif isinstance(step, dict):
            prepared.append(command_from_dict(step))
        else:
            raise ValueError("Unsupported step type")
    return prepared