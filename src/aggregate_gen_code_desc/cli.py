from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterator
from urllib.parse import unquote, urlparse

from aggregate_gen_code_desc.algorithm_a import collect_algorithm_a_lines
from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines
from aggregate_gen_code_desc.algorithm_c import collect_algorithm_c_lines
from aggregate_gen_code_desc.diagnostics import Logger
from aggregate_gen_code_desc.metrics import AggregateMetrics, GenerationLine, calculate_metrics
from aggregate_gen_code_desc.output import build_aggregate_record, write_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aggregateGenCodeDesc")
    parser.add_argument("--repoUrl", required=True)
    parser.add_argument("--repoBranch", required=True)
    parser.add_argument("--startTime", required=True)
    parser.add_argument("--endTime", required=True)
    parser.add_argument("--genCodeDescDir", required=True)
    parser.add_argument("--threshold", type=int, default=60)
    parser.add_argument("--algorithm", choices=["A", "B", "C"], default="C")
    parser.add_argument("--scope", choices=["A", "B", "C", "D"], default="A")
    parser.add_argument("--repoPath")
    parser.add_argument("--commitPatchDir")
    parser.add_argument("--blameWhitespace", choices=["respect", "ignore"], default="respect")
    parser.add_argument("--renameDetection", choices=["off", "basic", "aggressive"], default="basic")
    parser.add_argument("--onMissing", choices=["abort", "zero", "skip", "ignore"])
    parser.add_argument("--onDuplicate", choices=["reject", "last-wins"], default="reject")
    parser.add_argument("--onClockSkew", choices=["abort", "ignore"], default="abort")
    parser.add_argument(
        "--logLevel",
        choices=["Debug", "Info", "Warning", "Error", "DEBUG", "INFO", "WARN", "WARNING", "ERROR"],
        default="Info",
    )
    parser.add_argument("--outputDir", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logger = Logger(args.logLevel, stream=sys.stderr)

    try:
        logger.debug("CLI", f"algorithm={args.algorithm} scope={args.scope}")
        if args.algorithm == "A":
            with _algorithm_a_repo_path(args.repoUrl, args.repoPath, args.repoBranch) as repo_path:
                algorithm_result = collect_algorithm_a_lines(
                    gen_code_desc_dir=Path(args.genCodeDescDir),
                    repo_url=args.repoUrl,
                    repo_branch=args.repoBranch,
                    repo_path=repo_path,
                    start_time=args.startTime,
                    end_time=args.endTime,
                    scope=args.scope,
                    on_missing=args.onMissing or "zero",
                    on_duplicate=args.onDuplicate,
                    blame_whitespace=args.blameWhitespace,
                    rename_detection=args.renameDetection,
                )
        elif args.algorithm == "C":
            algorithm_result = collect_algorithm_c_lines(
                gen_code_desc_dir=Path(args.genCodeDescDir),
                repo_url=args.repoUrl,
                repo_branch=args.repoBranch,
                start_time=args.startTime,
                end_time=args.endTime,
                scope=args.scope,
                on_missing=args.onMissing or "abort",
                on_duplicate=args.onDuplicate,
                on_clock_skew=args.onClockSkew,
            )
        else:
            if args.commitPatchDir is None:
                raise ValueError("Algorithm B requires --commitPatchDir")
            algorithm_result = collect_algorithm_b_lines(
                gen_code_desc_dir=Path(args.genCodeDescDir),
                repo_url=args.repoUrl,
                repo_branch=args.repoBranch,
                commit_patch_dir=Path(args.commitPatchDir),
                start_time=args.startTime,
                end_time=args.endTime,
                scope=args.scope,
                on_missing=args.onMissing or "zero",
                on_duplicate=args.onDuplicate,
            )
        _emit_load_logs(logger, algorithm_result.diagnostics)
        metrics = calculate_metrics(algorithm_result.lines, threshold=args.threshold)
        aggregate_record = build_aggregate_record(
            lines=algorithm_result.lines,
            metrics=metrics,
            repo_url=args.repoUrl,
            repo_branch=args.repoBranch,
            start_time=args.startTime,
            end_time=args.endTime,
            algorithm=args.algorithm,
            scope=args.scope,
            threshold=args.threshold,
            input_protocol_version=algorithm_result.input_protocol_version,
            vcs_type=algorithm_result.vcs_type,
            diagnostics=algorithm_result.diagnostics,
        )
        _emit_process_logs(logger, args.algorithm, algorithm_result.lines, algorithm_result.diagnostics)
        write_outputs(Path(args.outputDir), aggregate_record, patch_text=getattr(algorithm_result, "patch_text", ""))
        _emit_summary_logs(logger, algorithm_result.lines, metrics, args.threshold)
        print(json.dumps(_build_stdout_metric_result(metrics, args.threshold), sort_keys=True))
    except Exception as error:
        logger.error("CLI", f"aggregateGenCodeDesc: {error}")
        return _exit_code_for_error(error)

    return 0


@contextlib.contextmanager
def _algorithm_a_repo_path(repo_url: str, repo_path_arg: str | None, repo_branch: str) -> Iterator[Path]:
    if repo_path_arg is not None:
        yield Path(repo_path_arg)
        return

    local_path = _local_repo_path_from_url(repo_url)
    if local_path is not None and _is_git_working_copy(local_path):
        yield local_path
        return

    with tempfile.TemporaryDirectory(prefix="aggregateGenCodeDesc-algA-") as temp_dir:
        clone_path = Path(temp_dir) / "repo"
        _clone_git_repo(repo_url, repo_branch, clone_path)
        yield clone_path


def _local_repo_path_from_url(repo_url: str) -> Path | None:
    parsed = urlparse(repo_url)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    if parsed.scheme == "":
        path = Path(repo_url)
        if path.exists():
            return path
    return None


def _is_git_working_copy(path: Path) -> bool:
    if not path.exists():
        return False
    completed = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        check=False,
        text=True,
        capture_output=True,
    )
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def _clone_git_repo(repo_url: str, repo_branch: str, clone_path: Path) -> None:
    completed = subprocess.run(
        ["git", "clone", "--branch", repo_branch, "--", repo_url, str(clone_path)],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or f"git clone exited {completed.returncode}"
        raise OSError(message)


def _exit_code_for_error(error: Exception) -> int:
    if _is_runtime_io_error(error):
        return 1
    if isinstance(error, ValueError):
        return 2
    return 1


def _is_runtime_io_error(error: Exception) -> bool:
    if isinstance(error, OSError):
        return True

    cause = error.__cause__
    while cause is not None:
        if isinstance(cause, OSError):
            return True
        cause = cause.__cause__

    return "VCS access failed" in str(error)


def _emit_load_logs(logger: Logger, diagnostics: dict) -> None:
    records_loaded = diagnostics.get("recordsLoaded", [])
    total_records = len(records_loaded)
    for index, record_summary in enumerate(records_loaded, start=1):
        logger.info(
            "LOAD",
            f"LOAD [{index}/{total_records}] revisionId={record_summary['revisionId']} entries={record_summary['entries']}",
        )
    for warning in diagnostics.get("warnings", []):
        logger.warn("LOAD", warning)


def _emit_process_logs(logger: Logger, algorithm: str, lines: list[GenerationLine], diagnostics: dict) -> None:
    record_count = len(diagnostics.get("recordsLoaded", []))
    logger.info("PROCESS", f"PROCESS algorithm={algorithm} records={record_count} lines={len(lines)}")
    file_groups = _lines_by_file(lines)
    for file_name, file_lines in file_groups.items():
        logger.debug("PROCESS", f"file={file_name} lines={len(file_lines)}")
        for line in file_lines:
            logger.debug(
                "PROCESS",
                f"file={file_name} line={line.line_number} genRatio={line.gen_ratio} method={line.gen_method}",
            )
    for process_detail in diagnostics.get("processDetails", []):
        logger.debug("PROCESS", process_detail)


def _emit_summary_logs(logger: Logger, lines: list[GenerationLine], metrics: AggregateMetrics, threshold: int) -> None:
    for file_name, file_lines in _lines_by_file(lines).items():
        file_metrics = calculate_metrics(file_lines, threshold=threshold)
        logger.info("SUMMARY", f"SUMMARY file={file_name} {_format_metrics(file_metrics)}")
    logger.info("SUMMARY", f"SUMMARY aggregate {_format_metrics(metrics)}")


def _lines_by_file(lines: list[GenerationLine]) -> dict[str, list[GenerationLine]]:
    file_groups: dict[str, list[GenerationLine]] = {}
    for line in lines:
        file_name = line.file_name or "<unknown>"
        file_groups.setdefault(file_name, []).append(line)
    return file_groups


def _format_metrics(metrics: AggregateMetrics) -> str:
    return (
        f"totalLines={metrics.total_lines} "
        f"weighted={metrics.weighted.value * 100:.1f}% "
        f"fullyAI={metrics.fully_ai.value * 100:.1f}% "
        f"mostlyAI={metrics.mostly_ai.value * 100:.1f}%"
    )


def _build_stdout_metric_result(metrics: AggregateMetrics, threshold: int) -> dict[str, object]:
    return {
        "totalLines": metrics.total_lines,
        "weighted": {"value": metrics.weighted.value, "numerator": metrics.weighted.numerator},
        "fullyAI": {"value": metrics.fully_ai.value, "numerator": metrics.fully_ai.numerator},
        "mostlyAI": {
            "value": metrics.mostly_ai.value,
            "numerator": metrics.mostly_ai.numerator,
            "threshold": threshold,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
