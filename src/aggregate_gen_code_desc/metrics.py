from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class GenerationLine:
    gen_ratio: int
    gen_method: str
    file_name: str | None = None
    line_number: int | None = None
    line_kind: str = "code"


@dataclass(frozen=True)
class MetricResult:
    value: float
    numerator: float


@dataclass(frozen=True)
class AggregateMetrics:
    total_lines: int
    weighted: MetricResult
    fully_ai: MetricResult
    mostly_ai: MetricResult


def calculate_metrics(lines: Iterable[GenerationLine], threshold: int) -> AggregateMetrics:
    if threshold < 0 or threshold > 100:
        raise ValueError("threshold must be between 0 and 100")

    materialized_lines = list(lines)
    total_lines = len(materialized_lines)
    for line in materialized_lines:
        if line.gen_ratio < 0 or line.gen_ratio > 100:
            raise ValueError("gen_ratio must be between 0 and 100")

    weighted_numerator = round(sum(line.gen_ratio / 100 for line in materialized_lines), 10)
    fully_ai_numerator = sum(1 for line in materialized_lines if line.gen_ratio == 100)
    mostly_ai_numerator = sum(1 for line in materialized_lines if line.gen_ratio >= threshold)

    if total_lines == 0:
        return AggregateMetrics(
            total_lines=0,
            weighted=MetricResult(value=0.0, numerator=0.0),
            fully_ai=MetricResult(value=0.0, numerator=0),
            mostly_ai=MetricResult(value=0.0, numerator=0),
        )

    return AggregateMetrics(
        total_lines=total_lines,
        weighted=MetricResult(value=round(weighted_numerator / total_lines, 10), numerator=weighted_numerator),
        fully_ai=MetricResult(value=round(fully_ai_numerator / total_lines, 10), numerator=fully_ai_numerator),
        mostly_ai=MetricResult(value=round(mostly_ai_numerator / total_lines, 10), numerator=mostly_ai_numerator),
    )
