from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aggregate_gen_code_desc.algorithm_a import CODE_EXTENSIONS, DOC_EXTENSIONS
from aggregate_gen_code_desc.metrics import GenerationLine
from aggregate_gen_code_desc.protocol import expand_entry_lines, load_gen_code_desc_dir, parse_utc_datetime


HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True)
class AlgorithmBResult:
    lines: list[GenerationLine]
    input_protocol_version: str
    vcs_type: str
    diagnostics: dict[str, Any]
    patch_text: str


def collect_algorithm_b_lines(
    gen_code_desc_dir: Path,
    repo_url: str,
    repo_branch: str,
    commit_patch_dir: Path,
    start_time: str,
    end_time: str,
    scope: str,
) -> AlgorithmBResult:
    if not commit_patch_dir.is_dir():
        raise ValueError(f"commit patch dir not found: {commit_patch_dir}")

    loaded = load_gen_code_desc_dir(gen_code_desc_dir, repo_url, repo_branch)
    if loaded.protocol_version != "26.03":
        raise ValueError("Algorithm B requires protocolVersion 26.03 input")

    replay_records, orphaned_revision_ids = _records_in_patch_history(loaded.records, commit_patch_dir)
    if not replay_records:
        raise ValueError("no genCodeDesc records match commitPatchDir patch history")

    start_dt = parse_utc_datetime(start_time)
    end_dt = parse_utc_datetime(end_time)
    snapshot: dict[str, list[LineOrigin]] = {}
    attribution_indexes: dict[str, dict[tuple[str, str, int], tuple[int, str]]] = {}
    revision_timestamps: dict[str, str] = {}
    patch_sections: list[tuple[str, str]] = []

    for record in _sort_records_for_replay(replay_records):
        repository = record["REPOSITORY"]
        revision_timestamp = repository.get("revisionTimestamp")
        if revision_timestamp is None:
            raise ValueError("Algorithm B requires REPOSITORY.revisionTimestamp for replay ordering")
        revision_dt = parse_utc_datetime(revision_timestamp)
        if revision_dt > end_dt:
            continue

        revision_id = repository["revisionId"]
        patch_path = commit_patch_dir / f"{revision_id}.patch"
        attribution_indexes[revision_id] = _build_v2603_attribution_index(record, scope)
        revision_timestamps[revision_id] = revision_timestamp
        snapshot = _replay_patch(
            snapshot=snapshot,
            patch_path=patch_path,
            revision_id=revision_id,
            revision_timestamp=revision_timestamp,
        )
        if start_dt <= revision_dt <= end_dt:
            patch_sections.append((revision_id, patch_path.read_text(encoding="utf-8")))

    lines = _collect_surviving_lines(
        snapshot=snapshot,
        attribution_indexes=attribution_indexes,
        revision_timestamps=revision_timestamps,
        start_time=start_time,
        end_time=end_time,
        scope=scope,
    )

    warnings = list(loaded.warnings)
    if orphaned_revision_ids:
        warnings.append(f"ignored orphaned genCodeDesc revisions absent from patch history: {', '.join(orphaned_revision_ids)}")

    vcs_type = replay_records[-1].get("REPOSITORY", {}).get("vcsType", "git")
    replay_revision_ids = {str(record["REPOSITORY"]["revisionId"]) for record in replay_records}
    return AlgorithmBResult(
        lines=lines,
        input_protocol_version=loaded.protocol_version,
        vcs_type=vcs_type,
        diagnostics={
            "missingRevisions": [],
            "duplicateRevisions": [],
            "clockSkewDetected": False,
            "warnings": warnings,
            "orphanedRevisions": orphaned_revision_ids,
            "lineOwnershipPolicy": _line_ownership_policy(),
            "recordsLoaded": [summary for summary in loaded.record_summaries if summary["revisionId"] in replay_revision_ids],
        },
        patch_text=_build_patch_artifact(
            repo_url=repo_url,
            repo_branch=repo_branch,
            start_time=start_time,
            end_time=end_time,
            scope=scope,
            patch_sections=patch_sections,
        ),
    )


def _records_in_patch_history(records: list[dict[str, Any]], commit_patch_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    patch_revision_ids = {
        path.name.removesuffix(".patch")
        for path in commit_patch_dir.glob("*.patch")
        if path.is_file() and path.name.endswith(".patch")
    }
    replay_records = []
    orphaned_revision_ids = []
    for record in records:
        revision_id = str(record["REPOSITORY"]["revisionId"])
        if revision_id in patch_revision_ids:
            replay_records.append(record)
        else:
            orphaned_revision_ids.append(revision_id)
    return replay_records, sorted(orphaned_revision_ids)


def _line_ownership_policy() -> dict[str, str]:
    return {
        "modifiedLines": "delete/add patch hunks transfer ownership to the commit that adds the current line form",
        "whitespaceOnlyChanges": "whitespace-only delete/add patch hunks transfer ownership; Algorithm B does not ignore whitespace",
        "lineEndingChanges": "file-wide line-ending replacement patches transfer ownership for each replaced line",
        "identicalReadd": "deleted and re-added identical content receives attribution from the re-add commit",
        "movedLines": "moved lines represented as delete/add patch hunks receive attribution from the move commit",
    }


@dataclass(frozen=True)
class LineOrigin:
    origin_revision_id: str | None
    origin_timestamp: str | None
    origin_file_name: str
    origin_line_number: int


@dataclass
class PatchHunk:
    old_start: int
    new_start: int
    lines: list[str] = field(default_factory=list)


@dataclass
class FilePatch:
    old_path: str | None = None
    new_path: str | None = None
    is_copy: bool = False
    hunks: list[PatchHunk] = field(default_factory=list)


def _sort_records_for_replay(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vcs_types = {str(record.get("REPOSITORY", {}).get("vcsType", "git")).lower() for record in records}
    if vcs_types == {"git"} and any(_parent_revision_ids(record) for record in records):
        return _sort_git_records_parent_first(records)
    if vcs_types == {"svn"}:
        return _sort_svn_records_by_revision(records)

    return _sort_records_by_timestamp(records)


def _sort_records_by_timestamp(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda record: (
            parse_utc_datetime(record["REPOSITORY"]["revisionTimestamp"]),
            str(record["REPOSITORY"]["revisionId"]),
        ),
    )


def _sort_git_records_parent_first(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records_by_revision = {str(record["REPOSITORY"]["revisionId"]): record for record in records}
    visited: set[str] = set()
    visiting: set[str] = set()
    sorted_records: list[dict[str, Any]] = []

    def visit(record: dict[str, Any]) -> None:
        revision_id = str(record["REPOSITORY"]["revisionId"])
        if revision_id in visited:
            return
        if revision_id in visiting:
            raise ValueError(f"cycle detected in git parentRevisionIds at revision {revision_id}")

        visiting.add(revision_id)
        for parent_revision_id in sorted(_parent_revision_ids(record)):
            parent_record = records_by_revision.get(parent_revision_id)
            if parent_record is not None:
                visit(parent_record)
        visiting.remove(revision_id)
        visited.add(revision_id)
        sorted_records.append(record)

    for record in _sort_records_by_timestamp(records):
        visit(record)

    return sorted_records


def _parent_revision_ids(record: dict[str, Any]) -> list[str]:
    repository = record.get("REPOSITORY", {})
    parent_revision_ids = repository.get("parentRevisionIds", [])
    if isinstance(parent_revision_ids, str):
        return [parent_revision_ids]
    return [str(parent_revision_id) for parent_revision_id in parent_revision_ids]


def _sort_svn_records_by_revision(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda record: (
            _svn_revision_number(str(record["REPOSITORY"]["revisionId"])),
            parse_utc_datetime(record["REPOSITORY"]["revisionTimestamp"]),
        ),
    )


def _svn_revision_number(revision_id: str) -> int:
    normalized_revision_id = revision_id[1:] if revision_id.startswith(("r", "R")) else revision_id
    if not normalized_revision_id.isdigit():
        raise ValueError(f"SVN revisionId must be numeric: {revision_id}")
    return int(normalized_revision_id)


def _build_v2603_attribution_index(record: dict[str, Any], scope: str) -> dict[tuple[str, str, int], tuple[int, str]]:
    index: dict[tuple[str, str, int], tuple[int, str]] = {}
    for file_detail in record.get("DETAIL", []):
        file_name = file_detail.get("fileName", "")
        for line_kind, collection_name in _collections_for_scope(scope):
            for entry in file_detail.get(collection_name, []):
                for line_number in expand_entry_lines(entry):
                    index[(file_name, line_kind, line_number)] = (int(entry["genRatio"]), str(entry["genMethod"]))
    return index


def _replay_patch(
    snapshot: dict[str, list[LineOrigin]],
    patch_path: Path,
    revision_id: str,
    revision_timestamp: str,
) -> dict[str, list[LineOrigin]]:
    if not patch_path.exists():
        raise ValueError(f"missing patch file: {patch_path}")

    next_snapshot = {file_name: list(lines) for file_name, lines in snapshot.items()}
    for file_patch in _parse_file_patches(patch_path):
        source_file = file_patch.old_path
        target_file = file_patch.new_path
        if source_file is None and target_file is None:
            continue

        old_file = source_file or target_file
        new_file = target_file or source_file
        old_lines = list(next_snapshot.get(old_file or "", []))
        if file_patch.is_copy and target_file is not None:
            copied_lines = _copy_lines_to_revision(
                source_lines=old_lines,
                target_file=target_file,
                revision_id=revision_id,
                revision_timestamp=revision_timestamp,
            )
            next_snapshot[target_file] = _apply_hunks(
                old_lines=copied_lines,
                hunks=file_patch.hunks,
                target_file=target_file,
                revision_id=revision_id,
                revision_timestamp=revision_timestamp,
            )
            continue

        replayed_lines = _apply_hunks(
            old_lines=old_lines,
            hunks=file_patch.hunks,
            target_file=new_file or "",
            revision_id=revision_id,
            revision_timestamp=revision_timestamp,
        )

        if target_file is None:
            if source_file is not None:
                next_snapshot.pop(source_file, None)
            continue

        if source_file is not None and source_file != target_file:
            next_snapshot.pop(source_file, None)
        next_snapshot[target_file] = replayed_lines

    return next_snapshot


def _parse_file_patches(patch_path: Path) -> list[FilePatch]:
    file_patches: list[FilePatch] = []
    current_file_patch: FilePatch | None = None
    current_hunk: PatchHunk | None = None

    for raw_line in patch_path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("diff --git "):
            if current_file_patch is not None:
                file_patches.append(current_file_patch)
            current_file_patch = FilePatch()
            current_hunk = None
            continue

        if current_file_patch is None:
            continue

        if raw_line.startswith("--- "):
            current_file_patch.old_path = _normalize_patch_path(raw_line.removeprefix("--- "))
            continue
        if raw_line.startswith("+++ "):
            current_file_patch.new_path = _normalize_patch_path(raw_line.removeprefix("+++ "))
            continue
        if raw_line.startswith("rename from "):
            current_file_patch.old_path = _normalize_patch_path(raw_line.removeprefix("rename from "))
            continue
        if raw_line.startswith("rename to "):
            current_file_patch.new_path = _normalize_patch_path(raw_line.removeprefix("rename to "))
            continue
        if raw_line.startswith("copy from "):
            current_file_patch.old_path = _normalize_patch_path(raw_line.removeprefix("copy from "))
            current_file_patch.is_copy = True
            continue
        if raw_line.startswith("copy to "):
            current_file_patch.new_path = _normalize_patch_path(raw_line.removeprefix("copy to "))
            current_file_patch.is_copy = True
            continue

        hunk_match = HUNK_HEADER.match(raw_line)
        if hunk_match:
            current_hunk = PatchHunk(old_start=int(hunk_match.group(1)), new_start=int(hunk_match.group(3)))
            current_file_patch.hunks.append(current_hunk)
            continue

        if current_hunk is None:
            continue
        if raw_line.startswith((" ", "+", "-")) and not raw_line.startswith(("+++", "---")):
            current_hunk.lines.append(raw_line)

    if current_file_patch is not None:
        file_patches.append(current_file_patch)

    return file_patches


def _apply_hunks(
    old_lines: list[LineOrigin],
    hunks: list[PatchHunk],
    target_file: str,
    revision_id: str,
    revision_timestamp: str,
) -> list[LineOrigin]:
    if not hunks:
        return old_lines

    replayed_lines: list[LineOrigin] = []
    old_cursor = 1

    for hunk in hunks:
        while old_cursor < hunk.old_start:
            replayed_lines.append(_existing_or_legacy_origin(old_lines, old_cursor, target_file))
            old_cursor += 1

        new_cursor = hunk.new_start
        for raw_line in hunk.lines:
            marker = raw_line[:1]
            if marker == " ":
                replayed_lines.append(_existing_or_legacy_origin(old_lines, old_cursor, target_file))
                old_cursor += 1
                new_cursor += 1
            elif marker == "-":
                old_cursor += 1
            elif marker == "+":
                replayed_lines.append(
                    LineOrigin(
                        origin_revision_id=revision_id,
                        origin_timestamp=revision_timestamp,
                        origin_file_name=target_file,
                        origin_line_number=new_cursor,
                    )
                )
                new_cursor += 1

    while old_cursor <= len(old_lines):
        replayed_lines.append(old_lines[old_cursor - 1])
        old_cursor += 1

    return replayed_lines


def _copy_lines_to_revision(
    source_lines: list[LineOrigin],
    target_file: str,
    revision_id: str,
    revision_timestamp: str,
) -> list[LineOrigin]:
    return [
        LineOrigin(
            origin_revision_id=revision_id,
            origin_timestamp=revision_timestamp,
            origin_file_name=target_file,
            origin_line_number=line_number,
        )
        for line_number, _source_line in enumerate(source_lines, start=1)
    ]


def _existing_or_legacy_origin(old_lines: list[LineOrigin], old_cursor: int, target_file: str) -> LineOrigin:
    if old_cursor <= len(old_lines):
        return old_lines[old_cursor - 1]
    return LineOrigin(
        origin_revision_id=None,
        origin_timestamp=None,
        origin_file_name=target_file,
        origin_line_number=old_cursor,
    )


def _collect_surviving_lines(
    snapshot: dict[str, list[LineOrigin]],
    attribution_indexes: dict[str, dict[tuple[str, str, int], tuple[int, str]]],
    revision_timestamps: dict[str, str],
    start_time: str,
    end_time: str,
    scope: str,
) -> list[GenerationLine]:
    start_dt = parse_utc_datetime(start_time)
    end_dt = parse_utc_datetime(end_time)
    lines: list[GenerationLine] = []

    for file_name in sorted(snapshot):
        line_kind = _line_kind_for_scope(file_name, scope)
        if line_kind is None:
            continue

        for line_number, origin in enumerate(snapshot[file_name], start=1):
            if origin.origin_revision_id is None or origin.origin_timestamp is None:
                continue
            origin_timestamp = revision_timestamps.get(origin.origin_revision_id, origin.origin_timestamp)
            origin_dt = parse_utc_datetime(origin_timestamp)
            if not start_dt <= origin_dt <= end_dt:
                continue

            attribution_index = attribution_indexes.get(origin.origin_revision_id, {})
            gen_ratio, gen_method = attribution_index.get(
                (origin.origin_file_name, line_kind, origin.origin_line_number),
                (0, "Manual"),
            )
            lines.append(
                GenerationLine(
                    gen_ratio=gen_ratio,
                    gen_method=gen_method,
                    file_name=file_name,
                    line_number=line_number,
                    line_kind=line_kind,
                )
            )

    return lines


def _build_patch_artifact(
    repo_url: str,
    repo_branch: str,
    start_time: str,
    end_time: str,
    scope: str,
    patch_sections: list[tuple[str, str]],
) -> str:
    parts = [
        f"# repoURL: {repo_url}\n",
        f"# repoBranch: {repo_branch}\n",
        f"# startTime: {start_time}\n",
        f"# endTime: {end_time}\n",
        "# algorithm: B\n",
        f"# scope: {scope}\n",
        f"# aggregateRevisionId: aggregate:{start_time}..{end_time}\n",
    ]
    for revision_id, patch_text in patch_sections:
        parts.append(f"# --- commit {revision_id} ---\n")
        parts.append(_ensure_trailing_newline(patch_text))
    return "".join(parts)


def _ensure_trailing_newline(text: str) -> str:
    if text.endswith("\n"):
        return text
    return f"{text}\n"


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