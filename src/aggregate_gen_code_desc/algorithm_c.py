from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aggregate_gen_code_desc.metrics import GenerationLine
from aggregate_gen_code_desc.protocol import (
    expand_entry_lines,
    expand_original_lines,
    load_gen_code_desc_dir,
    parse_utc_datetime,
)


@dataclass(frozen=True)
class AlgorithmCResult:
    lines: list[GenerationLine]
    input_protocol_version: str
    vcs_type: str
    diagnostics: dict[str, Any]


def collect_algorithm_c_lines(
    gen_code_desc_dir: Path,
    repo_url: str,
    repo_branch: str,
    start_time: str,
    end_time: str,
    scope: str,
) -> AlgorithmCResult:
    loaded = load_gen_code_desc_dir(gen_code_desc_dir, repo_url, repo_branch)
    if loaded.protocol_version != "26.04":
        raise ValueError("Algorithm C requires protocolVersion 26.04 input")

    start_dt = parse_utc_datetime(start_time)
    end_dt = parse_utc_datetime(end_time)
    surviving_lines: dict[tuple[str, str, int, str], GenerationLine] = {}
    sorted_records = sorted(
        loaded.records,
        key=lambda record: parse_utc_datetime(record["REPOSITORY"]["revisionTimestamp"]),
    )

    vcs_type = sorted_records[-1].get("REPOSITORY", {}).get("vcsType", "git")
    for record in sorted_records:
        revision_dt = parse_utc_datetime(record["REPOSITORY"]["revisionTimestamp"])
        if revision_dt > end_dt:
            continue
        delete_entries: list[tuple[dict[str, Any], str]] = []
        add_entries: list[tuple[dict[str, Any], str, str]] = []
        for file_detail in record.get("DETAIL", []):
            file_name = file_detail.get("fileName", "")
            for line_kind, collection_name in _collections_for_scope(scope):
                for entry in file_detail.get(collection_name, []):
                    if entry.get("changeType") == "delete":
                        delete_entries.append((entry, line_kind))
                    elif entry.get("changeType") == "add":
                        add_entries.append((entry, line_kind, file_name))

        for entry, line_kind in delete_entries:
            blame = entry["blame"]
            original_lines = expand_original_lines(blame, 1)
            for original_line in original_lines:
                key = (blame["revisionId"], blame["originalFilePath"], original_line, line_kind)
                surviving_lines.pop(key, None)

        for entry, line_kind, file_name in add_entries:
            line_numbers = expand_entry_lines(entry)
            blame = entry["blame"]
            original_lines = expand_original_lines(blame, len(line_numbers))
            for line_number, original_line in zip(line_numbers, original_lines, strict=True):
                key = (blame["revisionId"], blame["originalFilePath"], original_line, line_kind)
                surviving_lines[key] = GenerationLine(
                    gen_ratio=int(entry["genRatio"]),
                    gen_method=str(entry["genMethod"]),
                    file_name=file_name,
                    line_number=line_number,
                    line_kind=line_kind,
                )

    in_window_lines = []
    for key, line in surviving_lines.items():
        revision_id, original_file_path, original_line, line_kind = key
        timestamp = _find_surviving_timestamp(sorted_records, revision_id, original_file_path, original_line, line_kind, scope)
        if timestamp is None:
            continue
        timestamp_dt = parse_utc_datetime(timestamp)
        if start_dt <= timestamp_dt <= end_dt:
            in_window_lines.append(line)

    return AlgorithmCResult(
        lines=in_window_lines,
        input_protocol_version=loaded.protocol_version,
        vcs_type=vcs_type,
        diagnostics={"missingRevisions": [], "duplicateRevisions": [], "clockSkewDetected": False, "warnings": []},
    )


def _collections_for_scope(scope: str) -> list[tuple[str, str]]:
    if scope in {"A", "B"}:
        return [("code", "codeLines")]
    if scope == "C":
        return [("doc", "docLines")]
    if scope == "D":
        return [("code", "codeLines"), ("doc", "docLines")]
    raise ValueError("scope must be one of A, B, C, or D")


def _find_surviving_timestamp(
    records: list[dict[str, Any]],
    revision_id: str,
    original_file_path: str,
    original_line: int,
    line_kind: str,
    scope: str,
) -> str | None:
    for record in records:
        for file_detail in record.get("DETAIL", []):
            for candidate_kind, collection_name in _collections_for_scope(scope):
                if candidate_kind != line_kind:
                    continue
                for entry in file_detail.get(collection_name, []):
                    if entry.get("changeType") != "add":
                        continue
                    blame = entry.get("blame", {})
                    line_numbers = expand_entry_lines(entry)
                    original_lines = expand_original_lines(blame, len(line_numbers))
                    for candidate_original_line in original_lines:
                        if (
                            blame.get("revisionId") == revision_id
                            and blame.get("originalFilePath") == original_file_path
                            and candidate_original_line == original_line
                        ):
                            return blame.get("timestamp")
    return None
