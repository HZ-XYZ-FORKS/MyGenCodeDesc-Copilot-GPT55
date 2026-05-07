import json

from aggregate_gen_code_desc.algorithm_c import collect_algorithm_c_lines


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _record(revision_id, revision_timestamp, entries, total_code_lines=None):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.04",
        "codeAgent": "UnitTestingFixture",
        "SUMMARY": {
            "totalCodeLines": len(entries) if total_code_lines is None else total_code_lines,
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [{"fileName": "src/app.py", "codeLines": entries}],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _add_entry(revision_id, timestamp, line_from, line_to, gen_ratio, gen_method="codeCompletion"):
    return {
        "changeType": "add",
        "lineRange": {"from": line_from, "to": line_to},
        "genRatio": gen_ratio,
        "genMethod": gen_method,
        "blame": {
            "revisionId": revision_id,
            "originalFilePath": "src/app.py",
            "originalLine": line_from,
            "timestamp": timestamp,
        },
    }


def _delete_entry(origin_revision_id, origin_timestamp, line_from, line_to):
    return {
        "changeType": "delete",
        "lineRange": {"from": line_from, "to": line_to},
        "blame": {
            "revisionId": origin_revision_id,
            "originalFilePath": "src/app.py",
            "originalLine": line_from,
            "timestamp": origin_timestamp,
        },
    }


def _collect(gen_code_desc_dir):
    return collect_algorithm_c_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch="main",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )


# US-009 / AC-009-7 / Algorithm C add/delete surviving set / TC-UNIT-044
def test_algorithm_c_add_delete_operations_build_expected_surviving_set(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _record("c1", "2026-01-10T00:00:00Z", [_add_entry("c1", "2026-01-10T00:00:00Z", 1, 100, 100)]))
    _write_record(
        gen_code_desc_dir / "c2.json",
        _record(
            "c2",
            "2026-01-11T00:00:00Z",
            [
                _delete_entry("c1", "2026-01-10T00:00:00Z", 1, 20),
                _add_entry("c2", "2026-01-11T00:00:00Z", 101, 130, 60, "vibeCoding"),
            ],
        ),
    )
    _write_record(gen_code_desc_dir / "c3.json", _record("c3", "2026-01-12T00:00:00Z", [_delete_entry("c1", "2026-01-10T00:00:00Z", 21, 30)]))

    result = _collect(gen_code_desc_dir)

    assert len(result.lines) == 100
    assert sum(1 for line in result.lines if line.gen_ratio == 100) == 70
    assert sum(1 for line in result.lines if line.gen_ratio == 60) == 30


# US-009 / AC-009-8, AC-009-9 / duplicate add and SUMMARY mismatch diagnostics / TC-UNIT-045
def test_algorithm_c_duplicate_add_overwrites_later_entry_and_reports_warning(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _record("c1", "2026-01-10T00:00:00Z", [_add_entry("c1", "2026-01-10T00:00:00Z", 42, 42, 100)]))
    _write_record(gen_code_desc_dir / "c2.json", _record("c2", "2026-01-11T00:00:00Z", [_add_entry("c2", "2026-01-11T00:00:00Z", 42, 42, 40, "vibeCoding")], total_code_lines=500))

    result = _collect(gen_code_desc_dir)

    assert [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines] == [
        ("src/app.py", 42, 40, "vibeCoding")
    ]
    assert result.diagnostics["duplicateAddEntries"] == ["src/app.py:code:42 overwritten by revision c2"]
    assert any(
        "SUMMARY.partialGeneratedCodeLines expected 0 lines, found 1" in warning
        for warning in result.diagnostics["warnings"]
    )
