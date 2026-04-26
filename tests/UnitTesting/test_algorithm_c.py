import json

import pytest

from aggregate_gen_code_desc.algorithm_c import collect_algorithm_c_lines


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _v2604_record(revision_id, revision_timestamp, parent_revision_ids=None):
    repository = {
        "vcsType": "git",
        "repoURL": "https://example.test/repo",
        "repoBranch": "main",
        "revisionId": revision_id,
        "revisionTimestamp": revision_timestamp,
    }
    if parent_revision_ids is not None:
        repository["parentRevisionIds"] = parent_revision_ids

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
                "fileName": "src/auth.py",
                "codeLines": [
                    {
                        "changeType": "add",
                        "lineLocation": 1,
                        "genRatio": 100,
                        "genMethod": "codeCompletion",
                        "blame": {
                            "revisionId": revision_id,
                            "originalFilePath": "src/auth.py",
                            "originalLine": 1,
                            "timestamp": revision_timestamp,
                        },
                    }
                ],
            }
        ],
        "REPOSITORY": repository,
    }


# US-006 / AC-006-4 / Algorithm C clock skew / TC-UNIT-018
def test_algorithm_c_rejects_child_revision_timestamp_earlier_than_parent(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "parent.json", _v2604_record("parent", "2026-01-03T00:00:00Z"))
    _write_record(
        gen_code_desc_dir / "child.json",
        _v2604_record("child", "2026-01-02T00:00:00Z", parent_revision_ids=["parent"]),
    )

    with pytest.raises(ValueError, match="clock skew detected") as error:
        collect_algorithm_c_lines(
            gen_code_desc_dir=gen_code_desc_dir,
            repo_url="https://example.test/repo",
            repo_branch="main",
            start_time="2026-01-01T00:00:00Z",
            end_time="2026-01-31T00:00:00Z",
            scope="A",
        )

    assert "child" in str(error.value)
    assert "parent" in str(error.value)


# US-006 / AC-006-1 / Algorithm C missing parent chain break / TC-UNIT-038
def test_algorithm_c_rejects_missing_parent_revision_as_chain_break(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "child.json",
        _v2604_record("child", "2026-01-02T00:00:00Z", parent_revision_ids=["missing-parent"]),
    )

    with pytest.raises(ValueError, match="genCodeDesc chain break") as error:
        collect_algorithm_c_lines(
            gen_code_desc_dir=gen_code_desc_dir,
            repo_url="https://example.test/repo",
            repo_branch="main",
            start_time="2026-01-01T00:00:00Z",
            end_time="2026-01-31T00:00:00Z",
            scope="A",
        )

    assert "child" in str(error.value)
    assert "missing-parent" in str(error.value)
