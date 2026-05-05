from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aggregate_gen_code_desc.diagnostics import scale_policy
from aggregate_gen_code_desc.metrics import GenerationLine
from aggregate_gen_code_desc.protocol import expand_entry_lines, load_gen_code_desc_dir, parse_utc_datetime


CODE_EXTENSIONS = {".c", ".cc", ".cpp", ".cxx", ".go", ".h", ".hpp", ".java", ".js", ".py", ".rs", ".ts"}
DOC_EXTENSIONS = {".md", ".rst", ".txt"}


@dataclass(frozen=True)
class AlgorithmAResult:
    lines: list[GenerationLine]
    input_protocol_version: str
    vcs_type: str
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class BlameLine:
    revision_id: str
    original_file_path: str
    original_line: int
    current_file_path: str
    current_line: int
    timestamp: datetime


def collect_algorithm_a_lines(
    gen_code_desc_dir: Path,
    repo_url: str,
    repo_branch: str,
    repo_path: Path,
    end_rev: str,
    start_time: str,
    end_time: str,
    scope: str,
) -> AlgorithmAResult:
    loaded = load_gen_code_desc_dir(gen_code_desc_dir, repo_url, repo_branch)
    if loaded.protocol_version != "26.03":
        raise ValueError("Algorithm A requires protocolVersion 26.03 input")

    start_dt = parse_utc_datetime(start_time)
    end_dt = parse_utc_datetime(end_time)
    attribution_index = _build_v2603_attribution_index(loaded.records, scope)
    loaded_revision_ids = {str(record["REPOSITORY"]["revisionId"]) for record in loaded.records}
    missing_revision_ids: set[str] = set()
    lines: list[GenerationLine] = []
    process_details: list[str] = []

    try:
        for file_path, line_kind in _list_scoped_files(repo_path, end_rev, scope):
            for blame_line in _git_blame_lines(repo_path, end_rev, file_path):
                if not start_dt <= blame_line.timestamp <= end_dt:
                    continue
                if blame_line.revision_id not in loaded_revision_ids:
                    missing_revision_ids.add(blame_line.revision_id)
                gen_ratio, gen_method = attribution_index.get(
                    (blame_line.revision_id, blame_line.original_file_path, line_kind, blame_line.original_line),
                    (0, "Manual"),
                )
                process_details.append(
                    "algorithm=A "
                    f"file={blame_line.current_file_path} line={blame_line.current_line} "
                    f"state=BLAME origin={blame_line.revision_id} "
                    f"original={blame_line.original_file_path}:{blame_line.original_line} "
                    f"genRatio={gen_ratio} method={gen_method}"
                )
                lines.append(
                    GenerationLine(
                        gen_ratio=gen_ratio,
                        gen_method=gen_method,
                        file_name=blame_line.current_file_path,
                        line_number=blame_line.current_line,
                        line_kind=line_kind,
                    )
                )
    except RuntimeError as error:
        raise ValueError(_format_vcs_access_failure(repo_url, error)) from error

    vcs_type = loaded.records[-1].get("REPOSITORY", {}).get("vcsType", "git")
    return AlgorithmAResult(
        lines=lines,
        input_protocol_version=loaded.protocol_version,
        vcs_type=vcs_type,
        diagnostics={
            "missingRevisions": sorted(missing_revision_ids),
            "duplicateRevisions": [],
            "clockSkewDetected": False,
            "warnings": loaded.warnings,
            "scalePolicy": scale_policy(),
            "algorithmAPolicy": algorithm_a_policy(),
            "processDetails": process_details,
            "recordsLoaded": loaded.record_summaries,
        },
    )


def algorithm_a_policy() -> dict[str, str]:
    return {
        "renameDetection": "Algorithm A invokes git blame with -M so intra-file moved or renamed content can retain original attribution when Git can detect it",
        "copyMoveDetection": "Algorithm A invokes git blame with -C -C so cross-file moved or copied code can retain original attribution; this improves correctness but increases blame runtime on large histories",
        "vcsFailure": "Algorithm A requires local VCS access and aborts before output when Git commands fail; retry after VCS recovery or use Algorithm C when embedded blame is available",
    }


def _build_v2603_attribution_index(
    records: list[dict[str, Any]], scope: str
) -> dict[tuple[str, str, str, int], tuple[int, str]]:
    index: dict[tuple[str, str, str, int], tuple[int, str]] = {}
    for record in records:
        revision_id = record["REPOSITORY"]["revisionId"]
        for file_detail in record.get("DETAIL", []):
            file_name = file_detail.get("fileName", "")
            for line_kind, collection_name in _collections_for_scope(scope):
                for entry in file_detail.get(collection_name, []):
                    for line_number in expand_entry_lines(entry):
                        index[(revision_id, file_name, line_kind, line_number)] = (
                            int(entry["genRatio"]),
                            str(entry["genMethod"]),
                        )
    return index


def _list_scoped_files(repo_path: Path, end_rev: str, scope: str) -> list[tuple[str, str]]:
    output = _run_git(repo_path, "ls-tree", "-r", "--name-only", end_rev)
    scoped_files = []
    for file_path in output.splitlines():
        line_kind = _line_kind_for_scope(file_path, scope)
        if line_kind is not None:
            scoped_files.append((file_path, line_kind))
    return scoped_files


def _git_blame_lines(repo_path: Path, end_rev: str, file_path: str) -> list[BlameLine]:
    output = _run_git(repo_path, "blame", "-M", "-C", "-C", "--line-porcelain", end_rev, "--", file_path)
    lines: list[BlameLine] = []
    revision_id = ""
    original_file_path = file_path
    original_line = 0
    current_line = 0
    timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

    for raw_line in output.splitlines():
        if raw_line.startswith("\t"):
            lines.append(
                BlameLine(
                    revision_id=revision_id,
                    original_file_path=original_file_path,
                    original_line=original_line,
                    current_file_path=file_path,
                    current_line=current_line,
                    timestamp=timestamp,
                )
            )
            original_line += 1
            current_line += 1
            continue

        parts = raw_line.split()
        if len(parts) >= 4 and _looks_like_revision(parts[0]):
            revision_id = parts[0].lstrip("^")
            original_line = int(parts[1])
            current_line = int(parts[2])
            original_file_path = file_path
            continue
        if raw_line.startswith("author-time "):
            timestamp = datetime.fromtimestamp(int(raw_line.split()[1]), tz=timezone.utc)
            continue
        if raw_line.startswith("filename "):
            original_file_path = raw_line.removeprefix("filename ")

    return lines


def _run_git(repo_path: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError as error:
        raise RuntimeError(str(error)) from error
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or f"git {' '.join(args)} exited {completed.returncode}"
        raise RuntimeError(message)
    return completed.stdout.strip()


def _format_vcs_access_failure(repo_url: str, error: RuntimeError) -> str:
    return (
        f"Algorithm A VCS access failed for {repo_url}: {error}. "
        "retry after the VCS connection or local repository is available, or use Algorithm C when embedded blame is available."
    )


def _collections_for_scope(scope: str) -> list[tuple[str, str]]:
    if scope in {"A", "B"}:
        return [("code", "codeLines")]
    if scope == "C":
        return [("doc", "docLines")]
    if scope == "D":
        return [("code", "codeLines"), ("doc", "docLines")]
    raise ValueError("scope must be one of A, B, C, or D")


def _line_kind_for_scope(file_path: str, scope: str) -> str | None:
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


def _looks_like_revision(value: str) -> bool:
    candidate = value.lstrip("^")
    return len(candidate) >= 7 and all(character in "0123456789abcdefABCDEF" for character in candidate)
