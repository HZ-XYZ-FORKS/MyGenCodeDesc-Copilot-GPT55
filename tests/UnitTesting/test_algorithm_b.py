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


def _write_add_only_patch_for_file(path, file_name, total_lines=3):
    patch_lines = [
        f"diff --git a/{file_name} b/{file_name}",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        f"+++ b/{file_name}",
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


def _write_pure_rename_patch(path):
    _write_pure_rename_patch_for_paths(path, "src/auth.py", "src/account.py")


def _write_pure_rename_patch_for_paths(path, old_file_name, new_file_name):
    patch_lines = [
        f"diff --git a/{old_file_name} b/{new_file_name}",
        "similarity index 100%",
        f"rename from {old_file_name}",
        f"rename to {new_file_name}",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_delete_file_patch(path, file_name="src/auth.py", total_lines=3):
    patch_lines = [
        f"diff --git a/{file_name} b/{file_name}",
        "deleted file mode 100644",
        "index 1111111..0000000",
        f"--- a/{file_name}",
        "+++ /dev/null",
        f"@@ -1,{total_lines} +0,0 @@",
        *[f"-value_{line_number} = {line_number}" for line_number in range(1, total_lines + 1)],
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_pure_copy_patch(path, old_file_name="src/auth.py", new_file_name="src/auth_copy.py"):
    patch_lines = [
        f"diff --git a/{old_file_name} b/{new_file_name}",
        "similarity index 100%",
        f"copy from {old_file_name}",
        f"copy to {new_file_name}",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_rename_modify_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/account.py",
        "similarity index 66%",
        "rename from src/auth.py",
        "rename to src/account.py",
        "index 1111111..2222222 100644",
        "--- a/src/auth.py",
        "+++ b/src/account.py",
        "@@ -1,3 +1,3 @@",
        " value_1 = 1",
        "-value_2 = 2",
        "+value_2 = 20",
        " value_3 = 3",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_initial_multifile_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "new file mode 100644",
        "index 0000000..1111111",
        "--- /dev/null",
        "+++ b/src/auth.py",
        "@@ -0,0 +1,4 @@",
        "+auth_1 = 1",
        "+auth_2 = 2",
        "+auth_3 = 3",
        "+auth_4 = 4",
        "diff --git a/src/helper.py b/src/helper.py",
        "new file mode 100644",
        "index 0000000..2222222",
        "--- /dev/null",
        "+++ b/src/helper.py",
        "@@ -0,0 +1,3 @@",
        "+helper_1 = 1",
        "+helper_2 = 2",
        "+helper_3 = 3",
    ]
    path.write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def _write_multifile_multihunk_patch(path):
    patch_lines = [
        "diff --git a/src/auth.py b/src/auth.py",
        "index 1111111..3333333 100644",
        "--- a/src/auth.py",
        "+++ b/src/auth.py",
        "@@ -1,1 +1,1 @@",
        "-auth_1 = 1",
        "+auth_1 = 10",
        "@@ -4,1 +4,2 @@",
        "-auth_4 = 4",
        "+auth_4 = 40",
        "+auth_5 = 5",
        "diff --git a/src/helper.py b/src/helper.py",
        "index 2222222..4444444 100644",
        "--- a/src/helper.py",
        "+++ b/src/helper.py",
        "@@ -2,2 +2,2 @@",
        "-helper_2 = 2",
        "+helper_2 = 20",
        " helper_3 = 3",
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


def _v2603_multi_file_record_for_revision(revision_id, revision_timestamp, file_details, total_code_lines):
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
        "DETAIL": file_details,
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
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


# US-009 / AC-009-4 / Algorithm B multi-file multi-hunk replay / TC-UNIT-012
def test_algorithm_b_replays_every_file_section_and_hunk_in_a_patch(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_multi_file_record_for_revision(
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {
                    "fileName": "src/auth.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                        {"lineLocation": 4, "genRatio": 70, "genMethod": "vibeCoding"},
                    ],
                },
                {
                    "fileName": "src/helper.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 80, "genMethod": "vibeCoding"},
                        {"lineLocation": 3, "genRatio": 100, "genMethod": "codeCompletion"},
                    ],
                },
            ],
            7,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multi_file_record_for_revision(
            "rev2",
            "2026-01-11T00:00:00Z",
            [
                {
                    "fileName": "src/auth.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"},
                        {"lineLocation": 4, "genRatio": 90, "genMethod": "vibeCoding"},
                        {"lineLocation": 5, "genRatio": 100, "genMethod": "codeCompletion"},
                    ],
                },
                {
                    "fileName": "src/helper.py",
                    "codeLines": [
                        {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
                    ],
                },
            ],
            8,
        ),
    )
    _write_initial_multifile_patch(commit_patch_dir / "rev1.patch")
    _write_multifile_multihunk_patch(commit_patch_dir / "rev2.patch")

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
        ("src/auth.py", 1, 40, "vibeCoding"),
        ("src/auth.py", 2, 0, "Manual"),
        ("src/auth.py", 3, 0, "Manual"),
        ("src/auth.py", 4, 90, "vibeCoding"),
        ("src/auth.py", 5, 100, "codeCompletion"),
        ("src/helper.py", 1, 80, "vibeCoding"),
        ("src/helper.py", 2, 60, "vibeCoding"),
        ("src/helper.py", 3, 100, "codeCompletion"),
    ]
    assert metrics.total_lines == 8
    assert metrics.weighted.value == pytest.approx(0.5875)
    assert metrics.fully_ai.value == pytest.approx(0.25)
    assert metrics.mostly_ai.value == pytest.approx(0.625)
    assert "diff --git a/src/helper.py b/src/helper.py" in result.patch_text


# US-002 / AC-002-1, US-009 / AC-009-5 / Algorithm B pure rename / TC-UNIT-013
def test_algorithm_b_replays_pure_rename_without_double_counting_lines(tmp_path):
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
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multi_file_record_for_revision(
            "rev2",
            "2026-01-11T00:00:00Z",
            [],
            3,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=3)
    _write_pure_rename_patch(commit_patch_dir / "rev2.patch")

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
        ("src/account.py", 1, 100, "codeCompletion"),
        ("src/account.py", 2, 60, "vibeCoding"),
        ("src/account.py", 3, 0, "Manual"),
    ]
    assert metrics.total_lines == 3
    assert metrics.weighted.value == pytest.approx(0.5333333333)
    assert metrics.fully_ai.value == pytest.approx(0.3333333333)
    assert metrics.mostly_ai.value == pytest.approx(0.6666666667)


# US-002 / AC-002-2, US-009 / AC-009-5 / Algorithm B rename plus modify / TC-UNIT-014
def test_algorithm_b_replays_rename_plus_modify_with_changed_line_from_rename_commit(tmp_path):
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
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multi_file_record_for_revision(
            "rev2",
            "2026-01-11T00:00:00Z",
            [
                {
                    "fileName": "src/account.py",
                    "codeLines": [
                        {"lineLocation": 2, "genRatio": 40, "genMethod": "vibeCoding"},
                    ],
                }
            ],
            3,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=3)
    _write_rename_modify_patch(commit_patch_dir / "rev2.patch")

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
        ("src/account.py", 1, 100, "codeCompletion"),
        ("src/account.py", 2, 40, "vibeCoding"),
        ("src/account.py", 3, 0, "Manual"),
    ]
    assert metrics.total_lines == 3
    assert metrics.weighted.value == pytest.approx(0.4666666667)
    assert metrics.fully_ai.value == pytest.approx(0.3333333333)
    assert metrics.mostly_ai.value == pytest.approx(0.3333333333)


# US-009 / AC-009-5 / Algorithm B chained renames / TC-UNIT-015
def test_algorithm_b_tracks_unchanged_lines_through_chained_renames(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev1.json",
        _v2603_multi_file_record_for_revision(
            "rev1",
            "2026-01-10T00:00:00Z",
            [
                {
                    "fileName": "src/v1.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 100, "genMethod": "codeCompletion"},
                        {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
                    ],
                }
            ],
            3,
        ),
    )
    for revision_id, revision_timestamp in [
        ("rev2", "2026-01-11T00:00:00Z"),
        ("rev3", "2026-01-12T00:00:00Z"),
    ]:
        _write_record(
            gen_code_desc_dir / f"{revision_id}.json",
            _v2603_multi_file_record_for_revision(
                revision_id,
                revision_timestamp,
                [],
                3,
            ),
        )
    _write_add_only_patch_for_file(commit_patch_dir / "rev1.patch", "src/v1.py", total_lines=3)
    _write_pure_rename_patch_for_paths(commit_patch_dir / "rev2.patch", "src/v1.py", "src/v2.py")
    _write_pure_rename_patch_for_paths(commit_patch_dir / "rev3.patch", "src/v2.py", "src/v3.py")

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
        ("src/v3.py", 1, 100, "codeCompletion"),
        ("src/v3.py", 2, 60, "vibeCoding"),
        ("src/v3.py", 3, 0, "Manual"),
    ]
    assert metrics.total_lines == 3
    assert metrics.weighted.value == pytest.approx(0.5333333333)
    assert metrics.fully_ai.value == pytest.approx(0.3333333333)
    assert metrics.mostly_ai.value == pytest.approx(0.6666666667)


# US-002 / AC-002-3 / Algorithm B deleted file / TC-UNIT-016
def test_algorithm_b_excludes_deleted_file_from_final_snapshot(tmp_path):
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
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multi_file_record_for_revision(
            "rev2",
            "2026-01-11T00:00:00Z",
            [],
            0,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=3)
    _write_delete_file_patch(commit_patch_dir / "rev2.patch", total_lines=3)

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

    assert result.lines == []
    assert metrics.total_lines == 0
    assert metrics.weighted.value == pytest.approx(0.0)
    assert metrics.fully_ai.value == pytest.approx(0.0)
    assert metrics.mostly_ai.value == pytest.approx(0.0)


# US-002 / AC-002-4 / Algorithm B copied file / TC-UNIT-017
def test_algorithm_b_attributes_copied_file_to_copy_commit_and_keeps_source(tmp_path):
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
                {"lineLocation": 2, "genRatio": 60, "genMethod": "vibeCoding"},
            ],
            3,
        ),
    )
    _write_record(
        gen_code_desc_dir / "rev2.json",
        _v2603_multi_file_record_for_revision(
            "rev2",
            "2026-01-11T00:00:00Z",
            [
                {
                    "fileName": "src/auth_copy.py",
                    "codeLines": [
                        {"lineLocation": 1, "genRatio": 40, "genMethod": "vibeCoding"},
                        {"lineLocation": 2, "genRatio": 100, "genMethod": "codeCompletion"},
                        {"lineLocation": 3, "genRatio": 70, "genMethod": "vibeCoding"},
                    ],
                }
            ],
            6,
        ),
    )
    _write_add_only_patch(commit_patch_dir / "rev1.patch", total_lines=3)
    _write_pure_copy_patch(commit_patch_dir / "rev2.patch")

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
        ("src/auth_copy.py", 1, 40, "vibeCoding"),
        ("src/auth_copy.py", 2, 100, "codeCompletion"),
        ("src/auth_copy.py", 3, 70, "vibeCoding"),
    ]
    assert metrics.total_lines == 6
    assert metrics.weighted.value == pytest.approx(0.6166666667)
    assert metrics.fully_ai.value == pytest.approx(0.3333333333)
    assert metrics.mostly_ai.value == pytest.approx(0.6666666667)
