from types import SimpleNamespace

from aggregate_gen_code_desc import cli


# OVERVIEW
# [WHAT] UnitTesting for Algorithm A remote Git preparation in the CLI layer.
# [WHERE] `aggregate_gen_code_desc.cli._clone_git_repo` command construction.
# [WHY] Remote production repositories can be large; Algorithm A should prepare only the requested branch.
# SCOPE: Covers Git clone argument construction and failure guidance wrapping.
# OUT OF SCOPE: Networked provider integration and actual Git object transfer performance.
#
# UNIT TESTING DESIGN
# US-UNIT-001: As a maintainer running Algorithm A against a remote Git repository, I want clone preparation scoped to `repoBranch`, so that large hosted repositories do not fetch unnecessary branches.
# AC-UNIT-001: GIVEN a remote Git URL and target branch, WHEN the CLI prepares an Algorithm A working copy, THEN `git clone` uses `--single-branch` with the requested `--branch`.
#
# TEST CASE SPECIFICATIONS
# [@AC-UNIT-001,US-UNIT-001]
#  TC-UNIT-001 P3 Quality / Performance
#    @[Name]: verifyAlgARemoteClone_withTargetBranch_expectSingleBranchClone
#    @[Purpose]: Prevents remote AlgA preparation from scaling with unrelated repository branches.
#    @[Brief]: Captures the constructed `git clone` command without running Git.
#    @[Expect]: The command includes `--single-branch` and the requested branch before the URL separator.
#
# TODO/TRACKING
# - TC-UNIT-001: TODO -> RED -> GREEN


# UNIT TESTING IMPLEMENTATION
# [@TC-UNIT-001]
# @[Name]: verifyAlgARemoteClone_withTargetBranch_expectSingleBranchClone
# @[Steps]: SETUP subprocess capture -> BEHAVIOR clone helper -> VERIFY command shape -> CLEANUP monkeypatch
def test_algorithm_a_remote_clone_uses_single_requested_branch(monkeypatch, tmp_path):
    captured_commands = []

    def fake_run(command, **kwargs):
        captured_commands.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    cli._clone_git_repo("https://example.test/repo.git", "release/main", tmp_path / "repo")

    assert captured_commands == [
        (
            [
                "git",
                "clone",
                "--single-branch",
                "--branch",
                "release/main",
                "--",
                "https://example.test/repo.git",
                str(tmp_path / "repo"),
            ],
            {"check": False, "text": True, "capture_output": True},
        )
    ]