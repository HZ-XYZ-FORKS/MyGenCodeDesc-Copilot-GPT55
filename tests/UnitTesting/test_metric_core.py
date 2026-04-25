import pytest

from aggregate_gen_code_desc.metrics import GenerationLine, calculate_metrics


def _lines(gen_ratios):
    return [GenerationLine(gen_ratio=gen_ratio, gen_method="fixture") for gen_ratio in gen_ratios]


# US-001 / AC-001-1, AC-001-2, AC-001-3 / TC-UNIT-001
def test_core_metric_modes_for_mixed_authorship_lines():
    result = calculate_metrics(_lines([100, 100, 100, 100, 100, 80, 80, 80, 30, 0]), threshold=60)

    assert result.total_lines == 10
    assert result.weighted.value == pytest.approx(0.77)
    assert result.weighted.numerator == pytest.approx(7.7)
    assert result.fully_ai.value == pytest.approx(0.50)
    assert result.fully_ai.numerator == 5
    assert result.mostly_ai.value == pytest.approx(0.80)
    assert result.mostly_ai.numerator == 8


# US-001 / AC-001-4 / TC-UNIT-002
def test_core_metric_modes_for_all_human_lines():
    result = calculate_metrics(_lines([0] * 50), threshold=60)

    assert result.total_lines == 50
    assert result.weighted.value == pytest.approx(0.0)
    assert result.fully_ai.value == pytest.approx(0.0)
    assert result.mostly_ai.value == pytest.approx(0.0)


# US-001 / AC-001-5 / TC-UNIT-003
def test_core_metric_modes_for_all_fully_ai_lines():
    result = calculate_metrics(_lines([100] * 50), threshold=60)

    assert result.total_lines == 50
    assert result.weighted.value == pytest.approx(1.0)
    assert result.fully_ai.value == pytest.approx(1.0)
    assert result.mostly_ai.value == pytest.approx(1.0)


# US-001 / AC-001-6 / TC-UNIT-004
def test_core_metric_modes_for_zero_denominator():
    result = calculate_metrics([], threshold=60)

    assert result.total_lines == 0
    assert result.weighted.value == pytest.approx(0.0)
    assert result.weighted.numerator == pytest.approx(0.0)
    assert result.fully_ai.value == pytest.approx(0.0)
    assert result.fully_ai.numerator == 0
    assert result.mostly_ai.value == pytest.approx(0.0)
    assert result.mostly_ai.numerator == 0


# US-001 / AC-001-3 / TC-UNIT-005
def test_mostly_ai_uses_the_requested_threshold():
    result = calculate_metrics(_lines([100, 80, 59, 60, 0]), threshold=80)

    assert result.total_lines == 5
    assert result.mostly_ai.value == pytest.approx(0.40)
    assert result.mostly_ai.numerator == 2
