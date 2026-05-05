import json
import os
import subprocess

from aggregate_gen_code_desc.algorithm_a import collect_algorithm_a_lines


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


def _record(repo_url, revision_id, revision_timestamp):
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
            "repoURL": repo_url,
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": revision_timestamp,
        },
    }


def _line_summary(result):
    return [(line.file_name, line.line_number, line.gen_ratio, line.gen_method) for line in result.lines]


# US-006 / AC-006-1 / Algorithm A missing genCodeDesc revision / TC-UNIT-046
def test_algorithm_a_live_blame_marks_missing_gen_code_desc_revision_as_manual(tmp_path):
    repo_path = tmp_path / "repo"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    repo_path.mkdir()
    gen_code_desc_dir.mkdir()
    _run_git(repo_path, "init")
    _run_git(repo_path, "checkout", "-b", "main")
    source_dir = repo_path / "src"
    source_dir.mkdir()
    (source_dir / "main.py").write_text("known = True\n", encoding="utf-8")
    known_revision = _commit_all(repo_path, "known record", "2026-01-10T00:00:00+0000")
    (source_dir / "main.py").write_text("known = True\nmissing_record_line = True\n", encoding="utf-8")
    missing_revision = _commit_all(repo_path, "missing record", "2026-01-12T00:00:00+0000")
    _write_record(
        gen_code_desc_dir / "known.json",
        _record(str(repo_path), known_revision, "2026-01-10T00:00:00Z"),
    )

    result = collect_algorithm_a_lines(
        gen_code_desc_dir=gen_code_desc_dir,
        repo_url=str(repo_path),
        repo_branch="main",
        repo_path=repo_path,
        end_rev=missing_revision,
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-31T00:00:00Z",
        scope="A",
    )

    assert _line_summary(result) == [
        ("src/main.py", 1, 100, "codeCompletion"),
        ("src/main.py", 2, 0, "Manual"),
    ]
    assert result.diagnostics["missingRevisions"] == [missing_revision]
