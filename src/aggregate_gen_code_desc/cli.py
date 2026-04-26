from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aggregate_gen_code_desc.algorithm_a import collect_algorithm_a_lines
from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines
from aggregate_gen_code_desc.algorithm_c import collect_algorithm_c_lines
from aggregate_gen_code_desc.diagnostics import emit_log
from aggregate_gen_code_desc.metrics import calculate_metrics
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
    parser.add_argument("--endRev", default="HEAD")
    parser.add_argument("--commitPatchDir")
    parser.add_argument("--logLevel", choices=["DEBUG", "INFO", "WARN", "ERROR"], default="INFO")
    parser.add_argument("--outputDir", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.algorithm == "A":
            algorithm_result = collect_algorithm_a_lines(
                gen_code_desc_dir=Path(args.genCodeDescDir),
                repo_url=args.repoUrl,
                repo_branch=args.repoBranch,
                repo_path=Path(args.repoPath or args.repoUrl),
                end_rev=args.endRev,
                start_time=args.startTime,
                end_time=args.endTime,
                scope=args.scope,
            )
        elif args.algorithm == "C":
            algorithm_result = collect_algorithm_c_lines(
                gen_code_desc_dir=Path(args.genCodeDescDir),
                repo_url=args.repoUrl,
                repo_branch=args.repoBranch,
                start_time=args.startTime,
                end_time=args.endTime,
                scope=args.scope,
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
            )
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
        write_outputs(Path(args.outputDir), aggregate_record, patch_text=getattr(algorithm_result, "patch_text", ""))
    except Exception as error:
        emit_log(args.logLevel, "ERROR", "CLI", f"aggregateGenCodeDesc: {error}", stream=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
