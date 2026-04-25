import json

import pytest

from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines
from aggregate_gen_code_desc.metrics import calculate_metrics


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_add_only_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        "+++ b/src/auth.py",
        "@@ -0,0 +1,10 @@",
        *[f"+value_{line_number} = {line_number}" for line_number in range(1, 11)],
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _v2603_record():
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "UnitTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 10,
            "fullGeneratedCodeLines": 5,
            "partialGeneratedCodeLines": 4,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": "src/auth.py",
                "codeLines": [
                    {"lineRange": {"from": 1, "to": 5}, "genRatio": 100, "genMethod": "codeCompletion"},
                    {"lineRange": {"from": 6, "to": 8}, "genRatio": 80, "genMethod": "vibeCoding"},
                    {"lineLocation": 9, "genRatio": 30, "genMethod": "vibeCoding"},
                ],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": "patch123",
            "revisionTimestamp": "2026-01-10T00:00:00Z",
        },
    }


# US-001 / Algorithm B / TC-UNIT-007
def test_algorithm_b_replays_add_only_patch_and_joins_sparse_v2603_detail(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "patch123.json", _v2603_record())
    _write_add_only_patch(commit_patch_dir / "patch123.patch")

    result = collect_algorithm_b_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch="main",
        commit_patch_dir=commit_patch_dir,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )
    metrics = calculate_metrics(result.lines, threshold=60)

    assert result.input_protocol_version == "26.03"
    assert metrics.total_lines == 10
    assert metrics.weighted.value == pytest.approx(0.77)
    assert metrics.fully_ai.value == pytest.approx(0.5)
    assert metrics.mostly_ai.value == pytest.approx(0.8)