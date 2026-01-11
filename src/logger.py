import logging
from pathlib import Path
from typing import Optional

_logger: Optional[logging.Logger] = None
_log_path: Optional[Path] = None


def init_logger(log_path: Path) -> None:
    """Configure a module-level logger writing to the given path."""
    global _logger, _log_path
    _log_path = log_path
    _logger = logging.getLogger("voice_assistant")
    _logger.handlers.clear()
    _logger.setLevel(logging.INFO)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    _logger.addHandler(handler)
    _logger.propagate = False
    _logger.info("Logger initialized")


def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        raise RuntimeError("Logger not initialized; call init_logger first")
    return _logger


def log(message: str) -> None:
    """Convenience wrapper to log info-level messages."""
    logger = get_logger()
    logger.info(message)
