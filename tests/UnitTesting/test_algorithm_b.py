import json

import pytest

from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines
from aggregate_gen_code_desc.metrics import calculate_metrics


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_add_only_patch(path, total_lines=10):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        "+++ b/src/auth.py",
        f"@@ -0,0 +1,{total_lines} @@",
        *[f"+value_{line_number} = {line_number}" for line_number in range(1, total_lines + 1)],
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_modify_delete_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "index 1111111..2222222 100644",
        "--- a/src/auth.py",
        "+++ b/src/auth.py",
        "@@ -1,5 +1,5 @@",
        " value_1 = 1",
        "-value_2 = 2",
        "+value_2 = 20",
        " value_3 = 3",
        "-value_4 = 4",
        " value_5 = 5",
        "+value_6 = 6",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_single_line_modify_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "index 1111111..2222222 100644",
        "--- a/src/auth.py",
        "+++ b/src/auth.py",
        "@@ -1,1 +1,1 @@",
        "-value_1 = 1",
        "+value_1 = 20",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _v2603_record_for_revision(
    revision_id,
    revision_timestamp,
    code_lines,
    total_code_lines,
    parent_revision_ids=None,
    vcs_type="git",
    repo_branch="main",
):
    repository = {
        "vcsType": vcs_type,
        "repoURL": "https://example.test/repo",
        "repoBranch": repo_branch,
        "revisionId": revision_id,
        "revisionTimestamp": revision_timestamp,
    }
    if parent_revision_ids is not None:
        repository["parentRevisionIds"] = parent_revision_ids

    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "UnitTestingFixture",
        "SUMMARY": {
            "totalCodeLines": total_code_lines,
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": "src/auth.py",
                "codeLines": code_lines,
            }
        ],
        "REPOSITORY": repository,
    }


def _v2603_record():
    return _v2603_record_for_revision(
        "patch123",
        "2026-01-10T00:00:00Z",
        [
            {"lineRange": {"from": 1, "to": 5}, "genRatio": 100, "genMethod": "codeCompletion"},
            {"lineRange": {"from": 6, "to": 8}, "genRatio": 80, "genMethod": "vibeCoding"},
            {"lineLocation": 9, "genRatio": 30, "genMethod": "vibeCoding"},
        ],
        10,
    )


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


# US-001, US-009 / Algorithm B / TC-UNIT-008
def test_algorithm_b_replays_deletes_modifications_and_multiple_patches_to_final_snapshot(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_record_for_revision(
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                {"lineLocation": 2, "genRatio": 80, "genMethod": "vibeCoding"},
                {"lineLocation": 4, "genRatio": 100, "genMethod": "codeCompletion"},
            ],
            5,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_record_for_revision(
            "rev2",
            "2026-01-11T00:00:00Z",
            [
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
                {"lineLocation": 5, "genRatio": 100, "genMethod": "codeCompletion"},
            ],
            5,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=5)
    _write_modify_delete_patch(commit_patch_dir / "rev2.patch")

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

    assert [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines] == [
        ("src/auth.py", 1, 100, "codeCompletion"),
        ("src/auth.py", 2, 60, "vibeCoding"),
        ("src/auth.py", 3, 0, "Manual"),
        ("src/auth.py", 4, 0, "Manual"),
        ("src/auth.py", 5, 100, "codeCompletion"),
    ]
    assert metrics.total_lines == 5
    assert metrics.weighted.value == pytest.approx(0.52)
    assert metrics.fully_ai.value == pytest.approx(0.4)
    assert metrics.mostly_ai.value == pytest.approx(0.6)


# US-001, US-009 / Algorithm B / TC-UNIT-009
def test_algorithm_b_builds_ordered_patch_artifact_from_window_revisions(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_record_for_revision(
            "rev2",
            "2026-01-11T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            1,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_record_for_revision(
            "rev1",
            "2026-01-10T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            1,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=1)
    _write_modify_delete_patch(commit_patch_dir / "rev2.patch")

    result = collect_algorithm_b_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch="main",
        commit_patch_dir=commit_patch_dir,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )

    assert result.patch_text.startswith(
        "# repoURL: https://example.test/repo\n"
        "# repoBranch: main\n"
        "# startTime: 2026-01-01T00:00:00Z\n"
        "# endTime: 2026-01-31T00:00:00Z\n"
        "# algorithm: B\n"
        "# scope: A\n"
    )
    assert result.patch_text.index("# --- commit rev1 ---") < result.patch_text.index("# --- commit rev2 ---")
    assert "diff --git a/src/auth.py b/src/auth.py" in result.patch_text
    assert result.patch_text.endswith("\n")


# US-001, US-009 / Algorithm B Git ordering / TC-UNIT-010
def test_algorithm_b_replays_git_parent_before_child_even_when_timestamps_are_inverted(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "child.json",
        _v2603_record_for_revision(
            "child",
            "2026-01-10T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"}],
            1,
            parent_revision_ids=["parent"],
        ),
    )
    _write_record(
        gen_code_desc_dir / "parent.json",
        _v2603_record_for_revision(
            "parent",
            "2026-01-11T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            1,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "parent.patch", total_lines=1)
    _write_single_line_modify_patch(commit_patch_dir / "child.patch")

    result = collect_algorithm_b_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch="main",
        commit_patch_dir=commit_patch_dir,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )

    assert [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines] == [
        ("src/auth.py", 1, 40, "vibeCoding"),
    ]
    assert result.patch_text.index("# --- commit parent ---") < result.patch_text.index("# --- commit child ---")


# US-001, US-007, US-009 / Algorithm B SVN ordering / TC-UNIT-011
def test_algorithm_b_replays_svn_numeric_revisions_before_timestamp_order(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "10.json",
        _v2603_record_for_revision(
            "10",
            "2026-01-10T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"}],
            1,
            vcs_type="svn",
            repo_branch="trunk",
        ),
    )
    _write_record(
        gen_code_desc_dir / "2.json",
        _v2603_record_for_revision(
            "2",
            "2026-01-11T00:00:00Z",
            [{"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"}],
            1,
            vcs_type="svn",
            repo_branch="trunk",
        ),
    )
    _write_add_only_patch(commit_patch_dir / "2.patch", total_lines=1)
    _write_single_line_modify_patch(commit_patch_dir / "10.patch")

    result = collect_algorithm_b_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url="https://example.test/repo",
        repo_branch="trunk",
        commit_patch_dir=commit_patch_dir,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )

    assert result.vcs_type == "svn"
    assert [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines] == [
        ("src/auth.py", 1, 40, "vibeCoding"),
    ]
    assert result.patch_text.index("# --- commit 2 ---") < result.patch_text.index("# --- commit 10 ---")
