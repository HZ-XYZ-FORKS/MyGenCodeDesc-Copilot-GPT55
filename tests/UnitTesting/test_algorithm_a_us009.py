import json
import os
import subprocess
from datetime import datetime, timezone

import pytest

from aggregate_gen_code_desc import algorithm_a
from aggregate_gen_code_desc.algorithm_a import BlameLine, collect_algorithm_a_lines


def _run_git(repo_path, *args, env=None):
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _commit_all(repo_path, message, timestamp):
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": timestamp,
        "GIT_COMMITTER_DATE": timestamp,
    }
    _run_git(repo_path, "add", ".")
    _run_git(
        repo_path,
        "-c",
        "user.name=UnitTesting",
        "-c",
        "user.email=unit@example.test",
        "commit",
        "-m",
        message,
        env=env,
    )
    return _run_git(repo_path, "rev-parse", "HEAD")


def _write_record(path, record):
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _record(repo_url, revision_id, revision_timestamp, file_name, line_count, gen_ratio, gen_method="codeCompletion"):
    return {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "UnitTestingFixture",
        "SUMMARY": {
            "totalCodeLines": 1,
            "fullGeneratedCodeLines": 1 if gen_ratio == 100 else 0,
            "partialGeneratedCodeLines": 1 if 0 < gen_ratio < 100 else 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": [
            {
                "fileName": file_name,
                "codeLines": [
                    {
                        "lineRange": {"from": 1, "to": line_count},
                        "genRatio": gen_ratio,
                        "genMethod": gen_method,
                    }
                ],
            }
        ],
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": repo_url,
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _line_summary(result):
    return [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines]


# US-009 / Algorithm A origin-coordinate join contract / TC-UNIT-052
def test_algorithm_a_joins_v2603_detail_by_blame_origin_coordinates(monkeypatch, tmp_path):
    revision_id = "abcdef1234567890"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "origin.json",
        _record(str(tmp_path / "repo"), revision_id, "2026-01-10T00:00:00Z", "src/a.py", 2, 100),
    )

    monkeypatch.setattr(algorithm_a, "_list_scoped_files", lambda *_args: [("src/math_utils.py", "code")])
    monkeypatch.setattr(
        algorithm_a,
        "_blame_lines",
        lambda *_args: [
            BlameLine(
                revision_id=revision_id,
                original_file_path="src/a.py",
                original_line=2,
                current_file_path="src/math_utils.py",
                current_line=4,
                timestamp=datetime(2026, 1, 10, tzinfo=timezone.utc),
            )
        ],
    )
    monkeypatch.setattr(algorithm_a, "_build_git_patch_artifact", lambda *_args: "")

    result = collect_algorithm_a_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url=str(tmp_path / "repo"),
        repo_branch="main",
        repo_path=tmp_path / "repo",
        end_rev="HEAD",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )

    assert _line_summary(result) == [("src/math_utils.py", 4, 100, "codeCompletion")]
    assert result.diagnostics["processDetails"] == [
        f"algorithm=A file=src/math_utils.py line=4 state=BLAME origin={revision_id} original=src/a.py:2 genRatio=100 method=codeCompletion"
    ]


# US-009 / Algorithm A origin-coordinate policy diagnostics / TC-UNIT-053
def test_algorithm_a_policy_documents_origin_coordinate_join():
    assert "origin file path" in algorithm_a.algorithm_a_policy()["originCoordinateJoin"]
    assert "current endTime" in algorithm_a.algorithm_a_policy()["originCoordinateJoin"]


# US-009 / AC-009-1 / Algorithm A rename blame command / TC-UNIT-041
def test_algorithm_a_blame_command_enables_rename_detection(monkeypatch, tmp_path):
    captured_calls = []

    def fake_run_git(repo_path, *args):
        captured_calls.append((repo_path, args))
        return "abcdef1234567890 10 10 1\nauthor-time 1768003200\nfilename new_name.py\n\trenamed line"

    monkeypatch.setattr(algorithm_a, "_run_git", fake_run_git)

    blame_lines = algorithm_a._git_blame_lines(tmp_path, "HEAD", "new_name.py")

    assert captured_calls == [
        (tmp_path, ("blame", "-M", "-C", "-C", "--line-porcelain", "HEAD", "--", "new_name.py"))
    ]
    assert blame_lines[0].revision_id == "abcdef1234567890"
    assert blame_lines[0].original_file_path == "new_name.py"
    assert blame_lines[0].original_line == 10


# US-004 / AC-004-3, US-009 / AC-009-1 / Algorithm A configurable blame policy / TC-UNIT-051
def test_algorithm_a_blame_command_respects_userguide_detection_flags(monkeypatch, tmp_path):
    captured_calls = []

    def fake_run_git(repo_path, *args):
        captured_calls.append((repo_path, args))
        return "abcdef1234567890 1 1 1\nauthor-time 1768003200\nfilename app.py\n\tline"

    monkeypatch.setattr(algorithm_a, "_run_git", fake_run_git)

    algorithm_a._git_blame_lines(tmp_path, "HEAD", "app.py", blame_whitespace="ignore", rename_detection="off")
    algorithm_a._git_blame_lines(tmp_path, "HEAD", "app.py", blame_whitespace="respect", rename_detection="basic")
    algorithm_a._git_blame_lines(tmp_path, "HEAD", "app.py", blame_whitespace="respect", rename_detection="aggressive")

    assert captured_calls == [
        (tmp_path, ("blame", "-w", "--line-porcelain", "HEAD", "--", "app.py")),
        (tmp_path, ("blame", "-M", "--line-porcelain", "HEAD", "--", "app.py")),
        (tmp_path, ("blame", "-M", "-C", "-C", "--line-porcelain", "HEAD", "--", "app.py")),
    ]


# US-009 / AC-009-2 / Algorithm A cross-file move blame / TC-UNIT-042
def test_algorithm_a_uses_copy_detection_for_cross_file_moved_lines(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _run_git(repo_path, "init")
    _run_git(repo_path, "checkout", "-b", "main")
    source_dir = repo_path / "src"
    source_dir.mkdir()
    moved_lines = [f"moved_value_{line_number} = {line_number}" for line_number in range(1, 41)]
    (source_dir / "source.py").write_text("\n".join(moved_lines) + "\n", encoding="utf-8")
    original_revision = _commit_all(repo_path, "add source", "2026-01-10T00:00:00+0000")
    (source_dir / "source.py").write_text("", encoding="utf-8")
    (source_dir / "target.py").write_text("\n".join(moved_lines) + "\n", encoding="utf-8")
    move_revision = _commit_all(repo_path, "move source block", "2026-01-11T00:00:00+0000")
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "original.json",
        _record(str(repo_path), original_revision, "2026-01-10T00:00:00Z", "src/source.py", 40, 100),
    )
    _write_record(
        gen_code_desc_dir / "move.json",
        _record(str(repo_path), move_revision, "2026-01-11T00:00:00Z", "src/target.py", 40, 0, "Manual"),
    )

    result = collect_algorithm_a_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url=str(repo_path),
        repo_branch="main",
        repo_path=repo_path,
        end_rev=move_revision,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )

    assert _line_summary(result) == [("src/target.py", line_number, 100, "codeCompletion") for line_number in range(1, 41)]
    assert "-C -C" in result.diagnostics["algorithmAPolicy"]["copyMoveDetection"]


# US-009 / AC-009-3 / Algorithm A VCS access failure / TC-UNIT-043
def test_algorithm_a_reports_vcs_access_failure_with_retry_guidance(tmp_path):
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    gen_code_desc_dir.mkdir()
    _write_record(
        gen_code_desc_dir / "rev.json",
        _record("https://example.test/repo", "abcdef1234567890", "2026-01-10T00:00:00Z", "src/app.py", 1, 100),
    )

    with pytest.raises(ValueError, match="use Algorithm C") as error:
        collect_algorithm_a_lines(
            gen_code_desc_dir=gen_code_desc_dir,
            repo_url="https://example.test/repo",
            repo_branch="main",
            repo_path=tmp_path / "missing-repo",
            end_rev="HEAD",
            start_time="2026-01-01T00:00:00Z",
            end_time="2026-01-31T00:00:00Z",
            scope="A",
        )

    assert "https://example.test/repo" in str(error.value)
    assert "retry" in str(error.value)
