from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LoadedRecords:
    protocol_version: str
    records: list[dict[str, Any]]
    warnings: list[str]
    record_summaries: list[dict[str, Any]]


def parse_utc_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    return datetime.fromisoformat(value)


def load_json_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    text = strip_jsonc_comments(text)
    return json.loads(text)


def strip_jsonc_comments(text: str) -> str:
    output: list[str] = []
    in_string = False
    escaped = False
    index = 0

    while index < len(text):
        character = text[index]
        next_character = text[index + 1] if index + 1 < len(text) else ""

        if in_string:
            output.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue

        if character == '"':
            in_string = True
            output.append(character)
            index += 1
            continue

        if character == "/" and next_character == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue

        if character == "/" and next_character == "*":
            index += 2
            while index + 1 < len(text) and not (text[index] == "*" and text[index + 1] == "/"):
                if text[index] in "\r\n":
                    output.append(text[index])
                index += 1
            index += 2
            continue

        output.append(character)
        index += 1

    return "".join(output)


def load_gen_code_desc_dir(gen_code_desc_dir: Path, repo_url: str, repo_branch: str) -> LoadedRecords:
    paths = sorted(gen_code_desc_dir.glob("*.json"))
    if not paths:
        raise ValueError(f"no genCodeDesc JSON files found in {gen_code_desc_dir}")

    records = []
    for path in paths:
        record = load_json_file(path)
        _validate_gen_ratios(record, path)
        records.append(record)
    versions = {record.get("protocolVersion") for record in records}
    if len(versions) != 1:
        raise ValueError("mixed protocol versions are not supported")
    protocol_version = versions.pop()
    if not protocol_version:
        raise ValueError("protocolVersion is required")

    seen_revision_ids: set[str] = set()
    for record in records:
        repository = record.get("REPOSITORY", {})
        if repository.get("repoURL") != repo_url:
            raise ValueError("REPOSITORY.repoURL does not match requested repoUrl")
        if repository.get("repoBranch") != repo_branch:
            raise ValueError("REPOSITORY.repoBranch does not match requested repoBranch")
        revision_id = repository.get("revisionId")
        if not revision_id:
            raise ValueError("REPOSITORY.revisionId is required")
        if revision_id in seen_revision_ids:
            raise ValueError(f"duplicate revisionId: {revision_id}")
        seen_revision_ids.add(revision_id)

    return LoadedRecords(
        protocol_version=protocol_version,
        records=records,
        warnings=_summary_detail_warnings(records),
        record_summaries=[_record_summary(record) for record in records],
    )


def _summary_detail_warnings(records: list[dict[str, Any]]) -> list[str]:
    warnings = []
    for record in records:
        repository = record.get("REPOSITORY", {})
        revision_id = str(repository.get("revisionId", "<unknown>"))
        summary = record.get("SUMMARY", {})
        for summary_key, collection_name in (("totalCodeLines", "codeLines"), ("totalDocLines", "docLines")):
            if summary_key not in summary:
                continue
            expected_count = int(summary[summary_key])
            found_count = _record_entry_count(record, collection_name)
            if expected_count != found_count:
                warnings.append(
                    f"revisionId={revision_id} SUMMARY.{summary_key} expected {expected_count} entries, found {found_count}"
                )
    return warnings


def _record_summary(record: dict[str, Any]) -> dict[str, Any]:
    repository = record.get("REPOSITORY", {})
    return {
        "revisionId": str(repository.get("revisionId", "<unknown>")),
        "entries": _record_entry_count(record),
    }


def _record_entry_count(record: dict[str, Any], collection_name: str | None = None) -> int:
    total = 0
    for file_detail in record.get("DETAIL", []):
        if collection_name is None:
            total += len(file_detail.get("codeLines", []))
            total += len(file_detail.get("docLines", []))
        else:
            total += len(file_detail.get(collection_name, []))
    return total


def _validate_gen_ratios(record: dict[str, Any], path: Path) -> None:
    for file_detail in record.get("DETAIL", []):
        file_name = file_detail.get("fileName", "<unknown>")
        for collection_name in ("codeLines", "docLines"):
            for entry in file_detail.get(collection_name, []):
                if "genRatio" not in entry:
                    continue
                try:
                    gen_ratio = int(entry["genRatio"])
                except (TypeError, ValueError) as error:
                    raise ValueError(f"genRatio must be 0-100 in {path}: {file_name}") from error
                if gen_ratio < 0 or gen_ratio > 100:
                    raise ValueError(f"genRatio must be 0-100 in {path}: {file_name}")


def expand_entry_lines(entry: dict[str, Any]) -> list[int]:
    if "lineLocation" in entry:
        return [int(entry["lineLocation"])]
    if "lineRange" in entry:
        line_range = entry["lineRange"]
        return list(range(int(line_range["from"]), int(line_range["to"]) + 1))
    return []


def expand_original_lines(blame: dict[str, Any], count: int) -> list[int]:
    if "originalLineRange" in blame:
        original_range = blame["originalLineRange"]
        return list(range(int(original_range["from"]), int(original_range["to"]) + 1))
    original_line = int(blame["originalLine"])
    return list(range(original_line, original_line + count))
