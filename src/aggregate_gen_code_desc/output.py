from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aggregate_gen_code_desc.metrics import AggregateMetrics, GenerationLine


AGGREGATE_OUTPUT_FILENAME = "aggregatedGenCodeDescV26.03.json"


def build_aggregate_record(
    lines: list[GenerationLine],
    metrics: AggregateMetrics,
    repo_url: str,
    repo_branch: str,
    start_time: str,
    end_time: str,
    algorithm: str,
    scope: str,
    threshold: int,
    input_protocol_version: str,
    vcs_type: str,
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    code_lines = [line for line in lines if line.line_kind == "code"]
    doc_lines = [line for line in lines if line.line_kind == "doc"]

    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "aggregateGenCodeDesc",
        "SUMMARY": {
            "totalCodeLines": len(code_lines),
            "fullGeneratedCodeLines": _full_count(code_lines),
            "partialGeneratedCodeLines": _partial_count(code_lines),
            "totalDocLines": len(doc_lines),
            "fullGeneratedDocLines": _full_count(doc_lines),
            "partialGeneratedDocLines": _partial_count(doc_lines),
        },
        "DETAIL": _build_detail(lines),
        "REPOSITORY": {
            "vcsType": vcs_type,
            "repoURL": repo_url,
            "repoBranch": repo_branch,
            "revisionId": f"aggregate:{start_time}..{end_time}",
        },
        "AGGREGATE": {
            "window": {"startTime": start_time, "endTime": end_time},
            "parameters": {
                "algorithm": algorithm,
                "scope": scope,
                "threshold": threshold,
                "inputProtocolVersion": input_protocol_version,
            },
            "metrics": {
                "weighted": {"value": metrics.weighted.value, "numerator": metrics.weighted.numerator},
                "fullyAI": {"value": metrics.fully_ai.value, "numerator": metrics.fully_ai.numerator},
                "mostlyAI": {
                    "value": metrics.mostly_ai.value,
                    "numerator": metrics.mostly_ai.numerator,
                    "threshold": threshold,
                },
            },
            "diagnostics": diagnostics,
        },
    }


def write_outputs(output_dir: Path, aggregate_record: dict[str, Any], patch_text: str = "") -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / AGGREGATE_OUTPUT_FILENAME).write_text(
        json.dumps(aggregate_record, indent=2), encoding="utf-8"
    )
    (output_dir / "commitStart2EndTime.patch").write_text(patch_text, encoding="utf-8")


def _full_count(lines: list[GenerationLine]) -> int:
    return sum(1 for line in lines if line.gen_ratio == 100)


def _partial_count(lines: list[GenerationLine]) -> int:
    return sum(1 for line in lines if 0 < line.gen_ratio < 100)


def _build_detail(lines: list[GenerationLine]) -> list[dict[str, Any]]:
    by_file: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for line in lines:
        if line.gen_ratio <= 0 or line.file_name is None or line.line_number is None:
            continue
        file_bucket = by_file.setdefault(line.file_name, {"codeLines": [], "docLines": []})
        collection_name = "codeLines" if line.line_kind == "code" else "docLines"
        file_bucket[collection_name].append(
            {"lineLocation": line.line_number, "genRatio": line.gen_ratio, "genMethod": line.gen_method}
        )

    detail = []
    for file_name in sorted(by_file):
        file_detail: dict[str, Any] = {"fileName": file_name}
        if by_file[file_name]["codeLines"]:
            file_detail["codeLines"] = sorted(by_file[file_name]["codeLines"], key=lambda entry: entry["lineLocation"])
        if by_file[file_name]["docLines"]:
            file_detail["docLines"] = sorted(by_file[file_name]["docLines"], key=lambda entry: entry["lineLocation"])
        detail.append(file_detail)
    return detail
