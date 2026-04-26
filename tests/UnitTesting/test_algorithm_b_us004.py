import json

from aggregate_gen_code_desc.algorithm_b import collect_algorithm_b_lines


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _write_patch(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_add_file_patch(path, file_name, added_lines):
    _write_patch(
        path,
        [
            f"diff --git a/{file_name} b/{file_name}",
            "new file mode 100644",
            "index 0000000..1111111",
            "--- /dev/null",
            f"+++ b/{file_name}",
            f"@@ -0,0 +1,{len(added_lines)} @@",
            *[f"+{line}" for line in added_lines],
        ],
    )


def _write_modify_line_patch(path, file_name, old_line, new_line):
    _write_patch(
        path,
        [
            f"diff --git a/{file_name} b/{file_name}",
            "index 1111111..2222222 100644",
            f"--- a/{file_name}",
            f"+++ b/{file_name}",
            "@@ -1,1 +1,1 @@",
            f"-{old_line}",
            f"+{new_line}",
        ],
    )


def _write_replace_file_patch(path, file_name, old_lines, new_lines):
    _write_patch(
        path,
        [
            f"diff --git a/{file_name} b/{file_name}",
            "index 1111111..2222222 100644",
            f"--- a/{file_name}",
            f"+++ b/{file_name}",
            f"@@ -1,{len(old_lines)} +1,{len(new_lines)} @@",
            *[f"-{line}" for line in old_lines],
            *[f"+{line}" for line in new_lines],
        ],
    )


def _write_delete_then_readd_patch(path, file_name, line_text):
    _write_patch(
        path,
        [
            f"diff --git a/{file_name} b/{file_name}",
            "index 1111111..2222222 100644",
            f"--- a/{file_name}",
            f"+++ b/{file_name}",
            "@@ -1,1 +1,1 @@",
            f"-{line_text}",
            f"+{line_text}",
        ],
    )


def _write_move_line_patch(path, file_name):
    _write_patch(
        path,
        [
            f"diff --git a/{file_name} b/{file_name}",
            "index 1111111..2222222 100644",
            f"--- a/{file_name}",
            f"+++ b/{file_name}",
            "@@ -1,3 +1,3 @@",
            " keep_before()",
            "-x = compute()",
            " keep_after()",
            "+x = compute()",
        ],
    )


def _record(revision_id, revision_timestamp, file_name, code_lines, total_code_lines=None):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "UnitTestingFixture",
        "SUMMARY": {
            "totalCodeLines": total_code_lines if total_code_lines is not None else len(code_lines),
            "fullGeneratedCodeLines": 0,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [{"fileName": file_name, "codeLines": code_lines}],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": "https://example.test/repo",
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _line(line_number, gen_ratio, gen_method="codeCompletion"):
    return {"lineLocation": line_number, "genRatio": gen_ratio, "genMethod": gen_method}


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


# US-004 / AC-004-1 / human edit transfers ownership / TC-UNIT-026
def test_algorithm_b_human_edit_transfers_ai_line_to_manual_attribution(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _record("c1", "2026-01-10T00:00:00Z", "src/auth.py", [_line(1, 100)]))
    _write_record(gen_code_desc_dir / "c2.json", _record("c2", "2026-01-11T00:00:00Z", "src/auth.py", [_line(1, 0, "Manual")]))
    _write_add_file_patch(commit_patch_dir / "c1.patch", "src/auth.py", ["allowed = True"])
    _write_modify_line_patch(commit_patch_dir / "c2.patch", "src/auth.py", "allowed = True", "allowed = False")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [("src/auth.py", 1, 0, "Manual")]


# US-004 / AC-004-2 / AI rewrite transfers human line / TC-UNIT-027
def test_algorithm_b_ai_rewrite_transfers_manual_line_to_ai_attribution(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _record("c1", "2026-01-10T00:00:00Z", "src/utils.py", [_line(1, 0, "Manual")]))
    _write_record(gen_code_desc_dir / "c2.json", _record("c2", "2026-01-11T00:00:00Z", "src/utils.py", [_line(1, 100)]))
    _write_add_file_patch(commit_patch_dir / "c1.patch", "src/utils.py", ["return value"])
    _write_modify_line_patch(commit_patch_dir / "c2.patch", "src/utils.py", "return value", "return normalize(value)")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [("src/utils.py", 1, 100, "codeCompletion")]


# US-004 / AC-004-3 / whitespace policy / TC-UNIT-028
def test_algorithm_b_whitespace_only_patch_transfers_ownership_and_reports_policy(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _record("c1", "2026-01-10T00:00:00Z", "src/config.py", [_line(1, 100)]))
    _write_record(gen_code_desc_dir / "c2.json", _record("c2", "2026-01-11T00:00:00Z", "src/config.py", [_line(1, 0, "Manual")]))
    _write_add_file_patch(commit_patch_dir / "c1.patch", "src/config.py", ["enabled = True"])
    _write_modify_line_patch(commit_patch_dir / "c2.patch", "src/config.py", "enabled = True", "    enabled = True")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [("src/config.py", 1, 0, "Manual")]
    assert "delete/add" in result.diagnostics["lineOwnershipPolicy"]["whitespaceOnlyChanges"]


# US-004 / AC-004-4 / line-ending style replacement / TC-UNIT-029
def test_algorithm_b_file_wide_line_ending_patch_transfers_all_replaced_lines(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    old_lines = ["alpha = 1", "beta = 2", "gamma = 3"]
    new_lines = ["alpha = 1", "beta = 2", "gamma = 3"]
    _write_record(
        gen_code_desc_dir / "c1.json",
        _record("c1", "2026-01-10T00:00:00Z", "src/data.py", [_line(1, 100), _line(2, 60, "vibeCoding"), _line(3, 0, "Manual")]),
    )
    _write_record(
        gen_code_desc_dir / "c2.json",
        _record("c2", "2026-01-11T00:00:00Z", "src/data.py", [_line(1, 40, "vibeCoding"), _line(2, 40, "vibeCoding"), _line(3, 40, "vibeCoding")]),
    )
    _write_add_file_patch(commit_patch_dir / "c1.patch", "src/data.py", old_lines)
    _write_replace_file_patch(commit_patch_dir / "c2.patch", "src/data.py", old_lines, new_lines)

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [
        ("src/data.py", 1, 40, "vibeCoding"),
        ("src/data.py", 2, 40, "vibeCoding"),
        ("src/data.py", 3, 40, "vibeCoding"),
    ]


# US-004 / AC-004-5 / identical re-add gets new attribution / TC-UNIT-030
def test_algorithm_b_identical_deleted_and_readded_line_gets_new_attribution(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(gen_code_desc_dir / "c1.json", _record("c1", "2026-01-10T00:00:00Z", "src/auth.py", [_line(1, 100)]))
    _write_record(gen_code_desc_dir / "c2.json", _record("c2", "2026-01-11T00:00:00Z", "src/auth.py", [_line(1, 20, "vibeCoding")]))
    _write_add_file_patch(commit_patch_dir / "c1.patch", "src/auth.py", ["return 42"])
    _write_delete_then_readd_patch(commit_patch_dir / "c2.patch", "src/auth.py", "return 42")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [("src/auth.py", 1, 20, "vibeCoding")]


# US-004 / AC-004-6 / moved line gets new attribution / TC-UNIT-031
def test_algorithm_b_moved_line_gets_move_commit_attribution(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    commit_patch_dir = tmp_path / "patches"
    gen_code_desc_dir.mkdir()
    commit_patch_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "c1.json",
        _record("c1", "2026-01-10T00:00:00Z", "src/auth.py", [_line(1, 0, "Manual"), _line(2, 100), _line(3, 0, "Manual")]),
    )
    _write_record(gen_code_desc_dir / "c2.json", _record("c2", "2026-01-11T00:00:00Z", "src/auth.py", [_line(3, 60, "vibeCoding")]))
    _write_add_file_patch(commit_patch_dir / "c1.patch", "src/auth.py", ["keep_before()", "x = compute()", "keep_after()"])
    _write_move_line_patch(commit_patch_dir / "c2.patch", "src/auth.py")

    result = _collect(gen_code_desc_dir, commit_patch_dir)

    assert _line_summary(result) == [
        ("src/auth.py", 1, 0, "Manual"),
        ("src/auth.py", 2, 0, "Manual"),
        ("src/auth.py", 3, 60, "vibeCoding"),
    ]
