import json

from aggregate_gen_code_desc.algorithm_c import collect_algorithm_c_lines


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _v2604_record(revision_id, revision_timestamp):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.04",
        "codeAgent": "UnitTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 1,
            "fullGeneratedCodeLines": 1,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": "src/legacy.py",
                "codeLines": [
                    {
                        "changeType": "add",
                        "lineLocation": 1,
                        "genRatio": 100,
                        "genMethod": "codeCompletion",
                        "blame": {
                            "revisionId": revision_id,
                            "originalFilePath": "src/legacy.py",
                            "originalLine": 1,
                            "timestamp": revision_timestamp,
                        },
                    }
                ],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


# US-008 / AC-008-1, AC-008-2, AC-008-3 / scale policy and empty window / TC-UNIT-041
def test_algorithm_c_empty_window_returns_no_lines_and_reports_scale_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "legacy.json", _v2604_record("legacy", "2025-12-01T00:00:00Z"))

    result = collect_algorithm_c_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch="main",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )

    assert result.lines == []
    assert "correctness over speed" in result.diagnostics["scalePolicy"]["algorithmAReferenceScale"]
    assert "200 GB" in result.diagnostics["scalePolicy"]["algorithmCReferenceScale"]
    assert "0 commits" in result.diagnostics["scalePolicy"]["emptyWindow"]
