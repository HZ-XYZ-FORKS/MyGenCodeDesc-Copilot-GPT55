import json

from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_patch(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_add_file_patch(path):
    _write_patch(
        path,
        [
            "diff --git a/src/main.py b/src/main.py",
            "new file mode 100644",
            "index 0000000..1111111",
            "--- /dev/null",
            "+++ b/src/main.py",
            "@@ -0,0 +1,1 @@",
            "+known = True",
        ],
    )


def _write_missing_record_patch(path):
    _write_patch(
        path,
        [
            "diff --git a/src/main.py b/src/main.py",
            "index 1111111..2222222 100644",
            "--- a/src/main.py",
            "+++ b/src/main.py",
            "@@ -1,1 +1,2 @@",
            " known = True",
            "+missing_record_line = True",
        ],
    )


def _record(revision_id, revision_timestamp):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
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
                "fileName": "src/main.py",
                "codeLines": [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
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


def _collect(gen_code_desc_dir, commit_patch_dir):
    return collect_algorithm_b_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch="main",
        commit_patch_dir=commit_patch_dir,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )


def _line_summary(result):
    return [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines]


# US-006 / AC-006-1 / missing genCodeDesc revision becomes manual attribution / TC-UNIT-037
def test_algorithm_b_replays_patch_missing_gen_code_desc_as_manual_line(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _record("c1", "2026-01-10T00:00:00Z"))
    _write_add_file_patch(commit_patch_dir / "c1.patch")
    _write_missing_record_patch(commit_patch_dir / "c5.patch")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [
        ("src/main.py", 1, 100, "codeCompletion"),
        ("src/main.py", 2, 0, "Manual"),
    ]
    assert result.diagnostics["missingRevisions"] == ["c5"]
