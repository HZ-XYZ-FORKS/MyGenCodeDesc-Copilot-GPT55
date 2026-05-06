from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import TextIO


LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
LOG_LEVEL_ALIASES = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARN": "WARN",
    "WARNING": "WARN",
    "ERROR": "ERROR",
}


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


def scale_policy() -> dict[str, str]:
    return {
        "algorithmAReferenceScale": "Algorithm A reference-scale runs prioritize correctness over speed with sequential file/blame processing; peak memory below 1 GB is a target documented by this fork, not a synthetic-test benchmark",
        "algorithmCReferenceScale": "Algorithm C 200 GB reference-scale streaming is a documented open limitation in this fork; current processing loads records before timestamp-order accumulation and reports that limitation explicitly",
        "emptyWindow": "A window with 0 commits returns totalLines=0 and 0.0% for all metric modes without error",
        "ioFailure": "genCodeDesc read failures abort before output is written and report the file path plus revisionId=<unknown> when metadata cannot be read",
    }


def _normalize_level(level: str) -> str:
    normalized = LOG_LEVEL_ALIASES.get(level.upper())
    if normalized is None:
        raise ValueError("logLevel must be one of Debug, Info, Warning, Error")
    return normalized
