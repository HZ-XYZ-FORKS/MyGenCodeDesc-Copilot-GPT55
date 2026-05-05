from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


SUMMARY_KEYS = (
    "totalCodeLines",
    "fullGeneratedCodeLines",
    "partialGeneratedCodeLines",
    "totalDocLines",
    "fullGeneratedDocLines",
    "partialGeneratedDocLines",
)


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
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"unable to read genCodeDesc file {path}: revisionId=<unknown>: {error}") from error
    text = strip_jsonc_comments(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path.name}: {error.msg} at line {error.lineno} column {error.colno}") from error


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
        _validate_record_schema(record, path)
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
        if not _repo_branch_matches(repository, repo_branch):
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


def _repo_branch_matches(repository: dict[str, Any], requested_repo_branch: str) -> bool:
    record_repo_branch = repository.get("repoBranch")
    if record_repo_branch == requested_repo_branch:
        return True
    if str(repository.get("vcsType", "git")).lower() == "svn":
        return _normalize_svn_branch_path(str(record_repo_branch)) == _normalize_svn_branch_path(requested_repo_branch)
    return False


def _normalize_svn_branch_path(repo_branch: str) -> str:
    return repo_branch.strip("/")


def _validate_record_schema(record: dict[str, Any], path: Path) -> None:
    if not isinstance(record, dict):
        raise ValueError(f"genCodeDesc record in {path.name} must be an object")
    for field_name in ("protocolName", "protocolVersion", "codeAgent", "SUMMARY", "DETAIL", "REPOSITORY"):
        _require_field(record, field_name)

    protocol_name = _require_str(record, "protocolName")
    if protocol_name != "generatedTextDesc":
        raise ValueError("protocolName must be generatedTextDesc")
    protocol_version = _require_str(record, "protocolVersion")
    _require_str(record, "codeAgent")
    _validate_summary(_require_mapping(record, "SUMMARY"))
    _validate_repository(_require_mapping(record, "REPOSITORY"), protocol_version)
    _validate_detail(_require_list(record, "DETAIL"), protocol_version)


def _validate_summary(summary: dict[str, Any]) -> None:
    for summary_key in SUMMARY_KEYS:
        _require_int(summary, summary_key, f"SUMMARY.{summary_key}")


def _validate_repository(repository: dict[str, Any], protocol_version: str) -> None:
    for repository_key in ("vcsType", "repoURL", "repoBranch", "revisionId"):
        _require_str(repository, repository_key, f"REPOSITORY.{repository_key}")
    if protocol_version == "26.04":
        _require_str(repository, "revisionTimestamp", "REPOSITORY.revisionTimestamp")


def _validate_detail(detail: list[Any], protocol_version: str) -> None:
    for file_index, file_detail in enumerate(detail):
        file_path = f"DETAIL[{file_index}]"
        if not isinstance(file_detail, dict):
            raise ValueError(f"{file_path} must be an object")
        _require_str(file_detail, "fileName", f"{file_path}.fileName")
        for collection_name in ("codeLines", "docLines"):
            if collection_name not in file_detail:
                continue
            collection = _require_list(file_detail, collection_name, f"{file_path}.{collection_name}")
            for entry_index, entry in enumerate(collection):
                entry_path = f"{file_path}.{collection_name}[{entry_index}]"
                _validate_detail_entry(entry, entry_path, protocol_version)


def _validate_detail_entry(entry: Any, entry_path: str, protocol_version: str) -> None:
    if not isinstance(entry, dict):
        raise ValueError(f"{entry_path} must be an object")
    if protocol_version == "26.04":
        _validate_v2604_detail_entry(entry, entry_path)
        return
    _validate_line_selector(entry, entry_path)
    _require_field(entry, "genRatio", f"{entry_path}.genRatio")
    _require_str(entry, "genMethod", f"{entry_path}.genMethod")


def _validate_v2604_detail_entry(entry: dict[str, Any], entry_path: str) -> None:
    change_type = _require_str(entry, "changeType", f"{entry_path}.changeType")
    if change_type not in {"add", "delete"}:
        raise ValueError(f"{entry_path}.changeType must be add or delete")
    blame = _require_mapping(entry, "blame", f"{entry_path}.blame")
    _require_str(blame, "revisionId", f"{entry_path}.blame.revisionId")
    _require_str(blame, "originalFilePath", f"{entry_path}.blame.originalFilePath")
    _validate_original_line_selector(blame, f"{entry_path}.blame")
    if change_type == "add":
        _validate_line_selector(entry, entry_path)
        _require_field(entry, "genRatio", f"{entry_path}.genRatio")
        _require_str(entry, "genMethod", f"{entry_path}.genMethod")
        _require_str(blame, "timestamp", f"{entry_path}.blame.timestamp")


def _validate_line_selector(entry: dict[str, Any], entry_path: str) -> None:
    has_line_location = "lineLocation" in entry
    has_line_range = "lineRange" in entry
    if not has_line_location and not has_line_range:
        raise ValueError(f"{entry_path} must include lineLocation or lineRange")
    if has_line_location and has_line_range:
        raise ValueError(f"{entry_path} must not include both lineLocation and lineRange")
    if has_line_location:
        _require_int(entry, "lineLocation", f"{entry_path}.lineLocation")
    if has_line_range:
        _validate_range(_require_mapping(entry, "lineRange", f"{entry_path}.lineRange"), f"{entry_path}.lineRange")


def _validate_original_line_selector(blame: dict[str, Any], blame_path: str) -> None:
    has_original_line = "originalLine" in blame
    has_original_line_range = "originalLineRange" in blame
    if not has_original_line and not has_original_line_range:
        raise ValueError(f"{blame_path} must include originalLine or originalLineRange")
    if has_original_line and has_original_line_range:
        raise ValueError(f"{blame_path} must not include both originalLine and originalLineRange")
    if has_original_line:
        _require_int(blame, "originalLine", f"{blame_path}.originalLine")
    if has_original_line_range:
        _validate_range(
            _require_mapping(blame, "originalLineRange", f"{blame_path}.originalLineRange"),
            f"{blame_path}.originalLineRange",
        )


def _validate_range(value: dict[str, Any], field_path: str) -> None:
    start = _require_int(value, "from", f"{field_path}.from")
    end = _require_int(value, "to", f"{field_path}.to")
    if start > end:
        raise ValueError(f"{field_path}.from must be <= {field_path}.to")


def _require_field(container: dict[str, Any], key: str, field_path: str | None = None) -> Any:
    resolved_path = field_path or key
    if key not in container:
        raise ValueError(f"{resolved_path} is required")
    return container[key]


def _require_mapping(container: dict[str, Any], key: str, field_path: str | None = None) -> dict[str, Any]:
    resolved_path = field_path or key
    value = _require_field(container, key, resolved_path)
    if not isinstance(value, dict):
        raise ValueError(f"{resolved_path} must be an object")
    return value


def _require_list(container: dict[str, Any], key: str, field_path: str | None = None) -> list[Any]:
    resolved_path = field_path or key
    value = _require_field(container, key, resolved_path)
    if not isinstance(value, list):
        raise ValueError(f"{resolved_path} must be an array")
    return value


def _require_str(container: dict[str, Any], key: str, field_path: str | None = None) -> str:
    resolved_path = field_path or key
    value = _require_field(container, key, resolved_path)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{resolved_path} must be a string")
    return value


def _require_int(container: dict[str, Any], key: str, field_path: str | None = None) -> int:
    resolved_path = field_path or key
    value = _require_field(container, key, resolved_path)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{resolved_path} must be an integer")
    return value


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
