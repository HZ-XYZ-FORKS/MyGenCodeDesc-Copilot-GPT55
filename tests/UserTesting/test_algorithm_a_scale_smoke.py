import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


# OVERVIEW
# [WHAT] UserTesting scale smoke for Algorithm A over a local Git repository.
# [WHERE] Root CLI `aggregateGenCodeDesc.py` using v26.03 genCodeDesc, live Git blame, and multiple files.
# [WHY] Production readiness needs a deterministic local pressure test before provider-scale benchmarks.
# SCOPE: Covers multi-file live blame, aggregate denominator size, patch artifact output, and scale diagnostics.
# OUT OF SCOPE: Full 1K-commit reference benchmark, hosted provider latency, and memory profiling.
#
# USER TESTING DESIGN
# US-UAT-SCALE-001: As a maintainer, I want a deterministic Algorithm A scale smoke, so that local CI catches regressions before expensive provider-scale benchmark runs.
# AC-UAT-SCALE-001: GIVEN a local Git repository with many generated files and lines, WHEN Algorithm A runs through the root CLI, THEN every generated line is counted and the audit patch is written.
# AC-UAT-SCALE-002: GIVEN the scale smoke runs, WHEN diagnostics are emitted, THEN Algorithm A scale policy remains visible in aggregate output.
#
# TEST CASE SPECIFICATIONS
# [@AC-UAT-SCALE-001,US-UAT-SCALE-001]
#  TC-UAT-SCALE-001 P1 Functional / Boundary
#    @[Name]: verifyAlgAScaleSmoke_withMultiFileGeneratedSnapshot_expectAllLinesCounted
#    @[Purpose]: Proves the Algorithm A path handles more than toy single-file fixtures.
#    @[Brief]: Creates a configurable multi-file Git repository, writes matching v26.03 metadata, and runs the root CLI.
#    @[Expect]: The aggregate counts every generated line and writes the window patch.
# [@AC-UAT-SCALE-002,US-UAT-SCALE-001]
#  TC-UAT-SCALE-002 P3 Quality / Performance
#    @[Name]: verifyAlgAScaleSmoke_withDiagnostics_expectScalePolicyVisible
#    @[Purpose]: Keeps scale limitations visible to maintainers while benchmark coverage grows.
#    @[Brief]: Reads aggregate diagnostics from the same scale-smoke run.
#    @[Expect]: Algorithm A reference-scale policy text is present.
#
# TODO/TRACKING
# - TC-UAT-SCALE-001: TODO -> GREEN
# - TC-UAT-SCALE-002: TODO -> GREEN


def _run_git(repo_path, *args, env=None):
    completed = subprocess.run(["git", *args], cwd=repo_path, check=False, env=env, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _commit_all(repo_path, message, timestamp):
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": timestamp,
        "GIT_COMMITTER_DATE": timestamp,
        "GIT_AUTHOR_NAME": "ScaleSmoke",
        "GIT_AUTHOR_EMAIL": "scale-smoke@example.test",
        "GIT_COMMITTER_NAME": "ScaleSmoke",
        "GIT_COMMITTER_EMAIL": "scale-smoke@example.test",
    }
    _run_git(repo_path, "add", "-A", env=env)
    _run_git(repo_path, "commit", "-q", "-m", message, env=env)
    return _run_git(repo_path, "rev-parse", "HEAD")


def _run_root_cli(args):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "aggregateGenCodeDesc.py"), *args],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def _write_v2603_record(path, repo_path, revision_id, file_count, lines_per_file):
    detail = []
    for file_index in range(file_count):
        detail.append(
            {
                "fileName": f"src/generated_{file_index:03}.py",
                "codeLines": [
                    {"lineLocation": line_number, "genRatio": 100, "genMethod": "codeCompletion"}
                    for line_number in range(1, lines_per_file + 1)
                ],
            }
        )
    total_lines = file_count * lines_per_file
    record = {
        "protocolName": "generatedTextDesc",
        "protocolVersion": "26.03",
        "codeAgent": "ScaleSmokeFixture",
        "SUMMARY": {
            "totalCodeLines": total_lines,
            "fullGeneratedCodeLines": total_lines,
            "partialGeneratedCodeLines": 0,
            "totalDocLines": 0,
            "fullGeneratedDocLines": 0,
            "partialGeneratedDocLines": 0,
        },
        "DETAIL": detail,
        "REPOSITORY": {
            "vcsType": "git",
            "repoURL": str(repo_path),
            "repoBranch": "main",
            "revisionId": revision_id,
            "revisionTimestamp": "2026-01-10T00:00:00Z",
        },
    }
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


# USER TESTING IMPLEMENTATION
# [@TC-UAT-SCALE-001,@TC-UAT-SCALE-002]
# @[Name]: verifyAlgAScaleSmoke_withMultiFileGeneratedSnapshot_expectAllLinesCounted
# @[Steps]: SETUP multi-file Git repo and genCodeDesc -> BEHAVIOR run AlgA CLI -> VERIFY metrics, patch, diagnostics -> CLEANUP tmp_path
def test_alg_a_scale_smoke_counts_multi_file_generated_snapshot(tmp_path):
    file_count = int(os.environ.get("AGGREGATE_GCD_ALGA_SCALE_SMOKE_FILES", "8"))
    lines_per_file = int(os.environ.get("AGGREGATE_GCD_ALGA_SCALE_SMOKE_LINES_PER_FILE", "12"))
    repo_path = tmp_path / "repo"
    gen_code_desc_dir = tmp_path / "genCodeDesc"
    output_dir = tmp_path / "out"
    repo_path.mkdir()
    gen_code_desc_dir.mkdir()
    _run_git(repo_path, "init", "-q")
    _run_git(repo_path, "checkout", "-b", "main")
    (repo_path / "src").mkdir()
    for file_index in range(file_count):
        lines = [f"generated_{file_index}_{line_index} = True\n" for line_index in range(lines_per_file)]
        (repo_path / "src" / f"generated_{file_index:03}.py").write_text("".join(lines), encoding="utf-8")
    revision_id = _commit_all(repo_path, "add generated scale-smoke files", "2026-01-10T00:00:00+0000")
    _write_v2603_record(gen_code_desc_dir / f"{revision_id}.json", repo_path, revision_id, file_count, lines_per_file)

    completed = _run_root_cli(
        [
            "--repoUrl",
            str(repo_path),
            "--repoBranch",
            "main",
            "--startTime",
            "2026-01-01T00:00:00Z",
            "--endTime",
            "2026-01-31T00:00:00Z",
            "--genCodeDescDir",
            str(gen_code_desc_dir),
            "--algorithm",
            "A",
            "--scope",
            "A",
            "--repoPath",
            str(repo_path),
            "--outputDir",
            str(output_dir),
        ]
    )

    expected_lines = file_count * lines_per_file
    assert completed.returncode == 0, completed.stderr
    aggregate = json.loads((output_dir / "aggregatedGenCodeDescV26.03.json").read_text(encoding="utf-8"))
    patch_text = (output_dir / "commitStart2EndTime.patch").read_text(encoding="utf-8")
    assert aggregate["SUMMARY"]["totalCodeLines"] == expected_lines
    assert aggregate["SUMMARY"]["fullGeneratedCodeLines"] == expected_lines
    assert aggregate["AGGREGATE"]["metrics"]["weighted"]["value"] == 1.0
    assert "correctness over speed" in aggregate["AGGREGATE"]["diagnostics"]["scalePolicy"]["algorithmAReferenceScale"]
    assert "src/generated_000.py" in patch_text
    assert f"src/generated_{file_count - 1:03}.py" in patch_text