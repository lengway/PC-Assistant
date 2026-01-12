"""Global hotkey hook.

Call `register_hotkey` with a callback to start voice capture.
"""

import keyboard


def register_hotkey(hotkey: str, callback) -> None:
    keyboard.add_hotkey(hotkey, callback)


def clear_hotkeys() -> None:
    keyboard.unhook_all_hotkeys()
