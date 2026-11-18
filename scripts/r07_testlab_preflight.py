"""Read-only TestLab preflight for GAIA RAG R07.

Never deploys, creates directories, starts Docker, accesses Qdrant, or reads
secrets. Reports the minimum evidence needed before an authorized rollout.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_PARENT = Path("/home/ubuntu/gaia-test-lab-homologacao")
EXPECTED_REPO = "tight-knit-net/gaia-rag-mini"
EXPECTED_BRANCH = "feat/r07-office-knowledge-assimilation"


def safe_workspace(path: str, parent: Path = ALLOWED_PARENT) -> Path:
    """Require the dedicated R07 directory; prohibit escape by symlinks."""
    root = Path(path)
    if not root.is_absolute() or root.is_symlink():
        raise ValueError("WORKSPACE_MUST_BE_ABSOLUTE_NON_SYMLINK")
    if not root.name.startswith("gaia-rag-r07-"):
        raise ValueError("NOT_R07_WORKSPACE")
    if root.parent != parent:
        raise ValueError("OUTSIDE_APPROVED_TESTLAB_DIRECTORY")
    if root.exists() and root.resolve() != root:
        raise ValueError("WORKSPACE_SYMLINK_ESCAPE")
    return root


def safe_container_name(name: str) -> str:
    """Only inspect a R07-specific container; never other host projects."""
    if not name.startswith("gaia-rag-r07-") or len(name) > 90:
        raise ValueError("NOT_R07_CONTAINER")
    if any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name):
        raise ValueError("INVALID_CONTAINER")
    return name


def command(*args: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=8, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    return result.returncode == 0, result.stdout.strip()


def inspect(workspace: str, expected_head: str, container: str = "") -> dict:
    root = safe_workspace(workspace)
    if len(expected_head) != 40 or any(c not in "0123456789abcdef" for c in expected_head):
        raise ValueError("INVALID_SHA")
    output = {
        "report_version": "r07-testlab-preflight-v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "clock_origin": "datetime.now(timezone.utc) on executing host",
        "workspace_name": root.name,
        "workspace_present": root.is_dir(),
        "git_commit_matches_expected": False,
        "branch_matches_expected": False,
        "working_tree_clean": False,
        "container_present": False,
        "container_running": False,
        "isolated_network_mode": False,
        "read_only_rootfs": False,
        "published_ports_absent": False,
        "testlab_homologated": False,
        "mutation_performed": False,
        "blockers": [],
    }
    if not root.is_dir():
        output["blockers"].append("R07_WORKSPACE_NOT_INSTALLED")
        return output

    ok, git = command("git", "-C", str(root), "rev-parse", "--is-inside-work-tree")
    if not ok or git != "true":
        output["blockers"].append("NOT_A_GIT_CHECKOUT")
        return output
    ok, head = command("git", "-C", str(root), "rev-parse", "HEAD")
    output["git_commit_matches_expected"] = ok and head == expected_head
    ok, branch = command("git", "-C", str(root), "branch", "--show-current")
    output["branch_matches_expected"] = ok and branch == EXPECTED_BRANCH
    ok, changes = command("git", "-C", str(root), "status", "--porcelain")
    output["working_tree_clean"] = ok and changes == ""
    for field, reason in (
        ("git_commit_matches_expected", "R07_HEAD_MISMATCH"),
        ("branch_matches_expected", "R07_BRANCH_MISMATCH"),
        ("working_tree_clean", "R07_CHECKOUT_DIRTY"),
    ):
        if not output[field]:
            output["blockers"].append(reason)

    if not container:
        output["blockers"].append("R07_CONTAINER_NOT_SELECTED")
        return output
    name = safe_container_name(container)
    ok, raw = command("docker", "inspect", "--format",
                      "{{json .State.Running}}|{{.HostConfig.NetworkMode}}|"
                      "{{json .HostConfig.ReadonlyRootfs}}|{{json .NetworkSettings.Ports}}",
                      name)
    if not ok:
        output["blockers"].append("R07_CONTAINER_NOT_INSTALLED")
        return output
    parts = raw.split("|", 3)
    if len(parts) != 4:
        output["blockers"].append("DOCKER_INSPECT_UNEXPECTED")
        return output
    output["container_present"] = True
    output["container_running"] = parts[0] == "true"
    output["isolated_network_mode"] = parts[1] == "none"
    output["read_only_rootfs"] = parts[2] == "true"
    try:
        published = json.loads(parts[3])
        output["published_ports_absent"] = (
            published is None or
            isinstance(published, dict) and all(v is None for v in published.values())
        )
    except json.JSONDecodeError:
        output["published_ports_absent"] = False
    for field, reason in (
        ("container_running", "R07_CONTAINER_NOT_RUNNING"),
        ("isolated_network_mode", "R07_NETWORK_NOT_ISOLATED"),
        ("read_only_rootfs", "R07_ROOTFS_NOT_READONLY"),
        ("published_ports_absent", "R07_PUBLIC_PORTS_PRESENT"),
    ):
        if not output[field]:
            output["blockers"].append(reason)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--container", default="")
    args = parser.parse_args()
    result = inspect(args.workspace, args.head, args.container)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
