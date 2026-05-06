from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
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
    patch_text: str


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
    on_missing: str = "zero",
    on_duplicate: str = "reject",
    blame_whitespace: str = "respect",
    rename_detection: str = "aggressive",
) -> AlgorithmAResult:
    if on_missing not in {"abort", "zero", "skip"}:
        raise ValueError("Algorithm A onMissing must be abort, zero, or skip")
    loaded = load_gen_code_desc_dir(gen_code_desc_dir, repo_url, repo_branch, on_duplicate=on_duplicate)
    if loaded.protocol_version != "26.03":
        raise ValueError("Algorithm A requires protocolVersion 26.03 input")

    start_dt = parse_utc_datetime(start_time)
    end_dt = parse_utc_datetime(end_time)
    attribution_index = _build_v2603_attribution_index(loaded.records, scope)
    loaded_revision_ids = {str(record["REPOSITORY"]["revisionId"]) for record in loaded.records}
    vcs_type = str(loaded.records[-1].get("REPOSITORY", {}).get("vcsType", "git"))
    missing_revision_ids: set[str] = set()
    lines: list[GenerationLine] = []
    process_details: list[str] = []

    try:
        for file_path, line_kind in _list_scoped_files(repo_path, end_rev, scope, vcs_type):
            for blame_line in _blame_lines(repo_path, end_rev, file_path, vcs_type, blame_whitespace, rename_detection):
                if not start_dt <= blame_line.timestamp <= end_dt:
                    continue
                if blame_line.revision_id not in loaded_revision_ids:
                    missing_revision_ids.add(blame_line.revision_id)
                    if on_missing == "abort":
                        raise ValueError(f"missing genCodeDesc record for blamed revision: {blame_line.revision_id}")
                    if on_missing == "skip":
                        continue
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
        if vcs_type.lower() == "svn":
            patch_text = _build_svn_patch_artifact(repo_path, repo_url, repo_branch, start_time, end_time, end_rev, scope)
        else:
            patch_text = _build_git_patch_artifact(repo_path, repo_url, repo_branch, start_time, end_time, end_rev, scope)
    except RuntimeError as error:
        raise ValueError(_format_vcs_access_failure(repo_url, error)) from error

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
            "validationPolicy": {
                "onMissing": on_missing,
                "onDuplicate": on_duplicate,
                "blameWhitespace": blame_whitespace,
                "renameDetection": rename_detection,
            },
            "processDetails": process_details,
            "recordsLoaded": loaded.record_summaries,
        },
        patch_text=patch_text,
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


def _list_scoped_files(repo_path: Path, end_rev: str, scope: str, vcs_type: str = "git") -> list[tuple[str, str]]:
    if vcs_type.lower() == "svn":
        return _list_scoped_svn_files(repo_path, scope)
    output = _run_git(repo_path, "ls-tree", "-r", "--name-only", end_rev)
    scoped_files = []
    for file_path in output.splitlines():
        line_kind = _line_kind_for_scope(file_path, scope)
        if line_kind is not None:
            scoped_files.append((file_path, line_kind))
    return scoped_files


def _list_scoped_svn_files(repo_path: Path, scope: str) -> list[tuple[str, str]]:
    scoped_files = []
    for path in sorted(repo_path.rglob("*")):
        if not path.is_file() or ".svn" in path.parts:
            continue
        file_path = path.relative_to(repo_path).as_posix()
        line_kind = _line_kind_for_scope(file_path, scope)
        if line_kind is not None:
            scoped_files.append((file_path, line_kind))
    return scoped_files


def _blame_lines(
    repo_path: Path,
    end_rev: str,
    file_path: str,
    vcs_type: str,
    blame_whitespace: str,
    rename_detection: str,
) -> list[BlameLine]:
    if vcs_type.lower() == "svn":
        return _svn_blame_lines(repo_path, end_rev, file_path)
    return _git_blame_lines(repo_path, end_rev, file_path, blame_whitespace, rename_detection)


def _git_blame_lines(
    repo_path: Path,
    end_rev: str,
    file_path: str,
    blame_whitespace: str = "respect",
    rename_detection: str = "aggressive",
) -> list[BlameLine]:
    output = _run_git(repo_path, *_git_blame_args(end_rev, file_path, blame_whitespace, rename_detection))
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


def _git_blame_args(end_rev: str, file_path: str, blame_whitespace: str, rename_detection: str) -> list[str]:
    if blame_whitespace not in {"respect", "ignore"}:
        raise ValueError("blameWhitespace must be respect or ignore")
    if rename_detection not in {"off", "basic", "aggressive"}:
        raise ValueError("renameDetection must be off, basic, or aggressive")

    args = ["blame"]
    if blame_whitespace == "ignore":
        args.append("-w")
    if rename_detection in {"basic", "aggressive"}:
        args.append("-M")
    if rename_detection == "aggressive":
        args.extend(["-C", "-C"])
    args.extend(["--line-porcelain", end_rev, "--", file_path])
    return args


def _build_git_patch_artifact(
    repo_path: Path,
    repo_url: str,
    repo_branch: str,
    start_time: str,
    end_time: str,
    end_rev: str,
    scope: str,
) -> str:
    diff_text = _git_diff_for_window(repo_path, start_time, end_time, end_rev)
    header = [
        f"# repoURL: {repo_url}\n",
        f"# repoBranch: {repo_branch}\n",
        f"# startTime: {start_time}\n",
        f"# endTime: {end_time}\n",
        "# algorithm: A\n",
        f"# scope: {scope}\n",
        f"# aggregateRevisionId: aggregate:{start_time}..{end_time}\n",
    ]
    if diff_text and not diff_text.endswith("\n"):
        diff_text = f"{diff_text}\n"
    return "".join(header) + diff_text


def _build_svn_patch_artifact(
    repo_path: Path,
    repo_url: str,
    repo_branch: str,
    start_time: str,
    end_time: str,
    end_rev: str,
    scope: str,
) -> str:
    diff_text = _run_svn(repo_path, "diff", "-r", f"0:{end_rev}")
    header = [
        f"# repoURL: {repo_url}\n",
        f"# repoBranch: {repo_branch}\n",
        f"# startTime: {start_time}\n",
        f"# endTime: {end_time}\n",
        "# algorithm: A\n",
        f"# scope: {scope}\n",
        f"# aggregateRevisionId: aggregate:{start_time}..{end_time}\n",
    ]
    if diff_text and not diff_text.endswith("\n"):
        diff_text = f"{diff_text}\n"
    return "".join(header) + diff_text


def _git_diff_for_window(repo_path: Path, start_time: str, end_time: str, end_rev: str) -> str:
    start_dt = parse_utc_datetime(start_time)
    end_dt = parse_utc_datetime(end_time)
    commits = _git_commits_with_timestamps(repo_path, end_rev)
    target_revision = next((revision_id for revision_id, timestamp in commits if timestamp <= end_dt), end_rev)
    base_revision = next((revision_id for revision_id, timestamp in commits if timestamp < start_dt), None)
    if base_revision is None:
        base_revision = _empty_tree_hash(repo_path)
    return _run_git(repo_path, "diff", base_revision, target_revision)


def _git_commits_with_timestamps(repo_path: Path, end_rev: str) -> list[tuple[str, datetime]]:
    output = _run_git(repo_path, "log", "--format=%H%x00%cI", end_rev)
    commits = []
    for raw_line in output.splitlines():
        revision_id, timestamp = raw_line.split("\x00", maxsplit=1)
        commits.append((revision_id, parse_utc_datetime(timestamp)))
    return commits


def _empty_tree_hash(repo_path: Path) -> str:
    return _run_git(repo_path, "hash-object", "-t", "tree", "/dev/null")


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


def _svn_blame_lines(repo_path: Path, end_rev: str, file_path: str) -> list[BlameLine]:
    output = _run_svn(repo_path, "blame", "--xml", "-r", end_rev, file_path)
    root = ET.fromstring(output)
    lines: list[BlameLine] = []
    for entry in root.findall(".//entry"):
        commit = entry.find("commit")
        if commit is None:
            continue
        revision_id = commit.attrib.get("revision", "")
        date_text = commit.findtext("date")
        if not revision_id or date_text is None:
            continue
        current_line = int(entry.attrib["line-number"])
        lines.append(
            BlameLine(
                revision_id=revision_id,
                original_file_path=file_path,
                original_line=current_line,
                current_file_path=file_path,
                current_line=current_line,
                timestamp=parse_utc_datetime(date_text),
            )
        )
    return lines


def _run_svn(repo_path: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["svn", *args],
            cwd=repo_path,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError as error:
        raise RuntimeError(str(error)) from error
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or f"svn {' '.join(args)} exited {completed.returncode}"
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
