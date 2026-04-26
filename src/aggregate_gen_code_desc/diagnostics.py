from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import TextIO


LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}


class Logger:
    def __init__(self, level: str, stream: TextIO = sys.stderr) -> None:
        self.level = _normalize_level(level)
        self.stream = stream

    def emit(self, message_level: str, component: str, message: str) -> None:
        emit_log(self.level, message_level, component, message, stream=self.stream)

    def debug(self, component: str, message: str) -> None:
        self.emit("DEBUG", component, message)

    def info(self, component: str, message: str) -> None:
        self.emit("INFO", component, message)

    def warn(self, component: str, message: str) -> None:
        self.emit("WARN", component, message)

    def error(self, component: str, message: str) -> None:
        self.emit("ERROR", component, message)


def emit_log(
    configured_level: str,
    message_level: str,
    component: str,
    message: str,
    stream: TextIO = sys.stderr,
) -> None:
    normalized_configured_level = _normalize_level(configured_level)
    normalized_message_level = _normalize_level(message_level)
    if LOG_LEVELS[normalized_message_level] < LOG_LEVELS[normalized_configured_level]:
        return
    print(format_log(normalized_message_level, component, message), file=stream)


def format_log(level: str, component: str, message: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return f"{timestamp} [{_normalize_level(level)}] [{component}] {message}"


def _normalize_level(level: str) -> str:
    normalized = level.upper()
    if normalized not in LOG_LEVELS:
        raise ValueError(f"logLevel must be one of {', '.join(LOG_LEVELS)}")
    return normalized
