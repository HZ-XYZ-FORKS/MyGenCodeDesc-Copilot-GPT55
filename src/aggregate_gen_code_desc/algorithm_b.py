from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aggregate_gen_code_desc.algorithm_a import CODE_EXTENSIONS, DOC_EXTENSIONS
from aggregate_gen_code_desc.metrics import GenerationLine
from aggregate_gen_code_desc.protocol import expand_entry_lines, load_gen_code_desc_dir, parse_utc_datetime


HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class AlgorithmBResult:
    lines: list[GenerationLine]
    input_protocol_version: str
    vcs_type: str
    diagnostics: dict[str, Any]


def collect_algorithm_b_lines(
    gen_code_desc_dir: Path,
    repo_url: str,
    repo_branch: str,
    commit_patch_dir: Path,
    start_time: str,
    end_time: str,
    scope: str,
) -> AlgorithmBResult:
    loaded = load_gen_code_desc_dir(gen_code_desc_dir, repo_url, repo_branch)
    if loaded.protocol_version != "26.03":
        raise ValueError("Algorithm B requires protocolVersion 26.03 input")

    start_dt = parse_utc_datetime(start_time)
    end_dt = parse_utc_datetime(end_time)
    lines: list[GenerationLine] = []

    for record in _sort_records_for_replay(loaded.records):
        repository = record["REPOSITORY"]
        revision_timestamp = repository.get("revisionTimestamp")
        if revision_timestamp is None:
            raise ValueError("Algorithm B requires REPOSITORY.revisionTimestamp for replay ordering")
        revision_dt = parse_utc_datetime(revision_timestamp)
        if revision_dt > end_dt:
            continue

        revision_id = repository["revisionId"]
        attribution_index = _build_v2603_attribution_index(record, scope)
        for added_line in _parse_added_lines(commit_patch_dir / f"{revision_id}.patch", scope):
            if not start_dt <= revision_dt <= end_dt:
                continue
            gen_ratio, gen_method = attribution_index.get(
                (added_line.file_name, added_line.line_kind, added_line.line_number),
                (0, "Manual"),
            )
            lines.append(
                GenerationLine(
                    gen_ratio=gen_ratio,
                    gen_method=gen_method,
                    file_name=added_line.file_name,
                    line_number=added_line.line_number,
                    line_kind=added_line.line_kind,
                )
            )

    vcs_type = loaded.records[-1].get("REPOSITORY", {}).get("vcsType", "git")
    return AlgorithmBResult(
        lines=lines,
        input_protocol_version=loaded.protocol_version,
        vcs_type=vcs_type,
        diagnostics={"missingRevisions": [], "duplicateRevisions": [], "clockSkewDetected": False, "warnings": []},
    )


@dataclass(frozen=True)
class AddedPatchLine:
    file_name: str
    line_number: int
    line_kind: str


def _sort_records_for_replay(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda record: parse_utc_datetime(record["REPOSITORY"]["revisionTimestamp"]))


def _build_v2603_attribution_index(record: dict[str, Any], scope: str) -> dict[tuple[str, str, int], tuple[int, str]]:
    index: dict[tuple[str, str, int], tuple[int, str]] = {}
    for file_detail in record.get("DETAIL", []):
        file_name = file_detail.get("fileName", "")
        for line_kind, collection_name in _collections_for_scope(scope):
            for entry in file_detail.get(collection_name, []):
                for line_number in expand_entry_lines(entry):
                    index[(file_name, line_kind, line_number)] = (int(entry["genRatio"]), str(entry["genMethod"]))
    return index


def _parse_added_lines(patch_path: Path, scope: str) -> list[AddedPatchLine]:
    if not patch_path.exists():
        raise ValueError(f"missing patch file: {patch_path}")

    added_lines: list[AddedPatchLine] = []
    current_file: str | None = None
    current_line_number: int | None = None

    for raw_line in patch_path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("+++ "):
            current_file = _normalize_patch_path(raw_line.removeprefix("+++ "))
            continue

        hunk_match = HUNK_HEADER.match(raw_line)
        if hunk_match:
            current_line_number = int(hunk_match.group(1))
            continue

        if current_file is None or current_line_number is None:
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            line_kind = _line_kind_for_scope(current_file, scope)
            if line_kind is not None and raw_line[1:].strip():
                added_lines.append(AddedPatchLine(current_file, current_line_number, line_kind))
            current_line_number += 1
            continue
        if raw_line.startswith("-") and not raw_line.startswith("---"):
            continue
        if raw_line.startswith(" "):
            current_line_number += 1

    return added_lines


def _normalize_patch_path(path: str) -> str | None:
    if path == "/dev/null":
        return None
    if path.startswith("b/") or path.startswith("a/"):
        return path[2:]
    return path


def _collections_for_scope(scope: str) -> list[tuple[str, str]]:
    if scope in {"A", "B"}:
        return [("code", "codeLines")]
    if scope == "C":
        return [("doc", "docLines")]
    if scope == "D":
        return [("code", "codeLines"), ("doc", "docLines")]
    raise ValueError("scope must be one of A, B, C, or D")


def _line_kind_for_scope(file_path: str | None, scope: str) -> str | None:
    if file_path is None:
        return None
    extension = Path(file_path).suffix
    if scope in {"A", "B"} and extension in CODE_EXTENSIONS:
        return "code"
    if scope == "C" and extension in DOC_EXTENSIONS:
        return "doc"
    if scope == "D" and extension in CODE_EXTENSIONS:
        return "code"
    if scope == "D" and extension in DOC_EXTENSIONS:
        return "doc"
    return None