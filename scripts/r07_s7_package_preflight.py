"""S7: static package attestations only; never builds/deploys/reaches servers.

The pinned base-image digest and installed package versions originate from a
previously passing GitHub Actions run; hash-locked wheels and vulnerability
scans remain a SEPARATE operational gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import re
from pathlib import Path

BASE = "python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b"
REQUIRED = {"mcp", "pyjwt", "uvicorn", "cryptography"}


def parse_lock(text: str) -> dict[str, str]:
    distributions = {}
    for line in text.splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)(?:\[crypto\])?==([0-9][A-Za-z0-9_.+!-]*)(?:\s+--hash=sha256:[a-f0-9]{64})?",
            item,
        )
        if not match:
            raise ValueError("FLOATING_OR_UNSAFE_DEPENDENCY")
        name = match.group(1).lower().replace("_", "-")
        if name in distributions:
            raise ValueError("DUPLICATE_DEPENDENCY")
        distributions[name] = match.group(2)
    if len(distributions) < 25 or not REQUIRED <= distributions.keys():
        raise ValueError("INCOMPLETE_DEPENDENCY_LOCK")
    return distributions


def inspect(root: Path) -> dict:
    docker = (root / "Dockerfile").read_text(encoding="utf-8")
    lock = (root / "requirements.lock").read_bytes()
    distributions = parse_lock(lock.decode("utf-8"))
    dockerignore = (root / ".dockerignore").read_text(encoding="utf-8")
    ghcr = (root / ".github/workflows/rag-ghcr-image.yml").read_text(encoding="utf-8")
    linode = (root / ".github/workflows/rag-linode-staging.yml").read_text(encoding="utf-8")
    compose = (root / ".github/deploy/linode/compose.staging.yml").read_text(
        encoding="utf-8")
    checks = {
        "base_image_digest_pinned": f"FROM {BASE}" in docker,
        "s9_hashed_binary_wheels": (
            "--require-hashes --only-binary=:all:" in docker
            and all(
                " --hash=sha256:" in line
                and len(line.split(" --hash=sha256:")[-1]) == 64
                for line in lock.decode("utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            )
        ),
        "dependency_install_version_locked": (
            "pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.lock" in docker
            and "python -m pip check" in docker
        ),
        "nonroot_runtime": "USER 10001:10001" in docker,
        "no_access_logs": '"--no-access-log"' in docker,
        "container_secrets_not_baked": (
            all(f"ENV {key}" not in docker for key in (
                "QDRANT_API_KEY", "CF_ACCESS_AUD",
                "GAIA_RAG_CSRF_SECRET", "GROQ_API_KEY",
            ))
            and "COPY secrets/" not in docker
            and "COPY . ." not in docker
        ),
        "sensitive_files_ignored": all(
            item in dockerignore
            for item in (".env", ".env.*", "*.key", "*.pem", "*.sqlite3",
                         "backups/", "state/", "secrets/")
        ),
        "publish_and_deploy_remain_frozen": (
            "if: " + "${{ false }}" in ghcr and
            "if: " + "${{ false }}" in linode
        ),
        "historical_compose_local_only": (
            '127.0.0.1:18081:8000' in compose
            and "read_only: true" in compose
            and "gaia_rag_review_state:/state" in compose
            and "tmpfs:" in compose
            and "cap_drop:" in compose
        ),
    }
    return {
        "scope": "S7_PACKAGE_STATIC_ONLY",
        "checks": checks,
        "pass": all(checks.values()),
        "dependency_count": len(distributions),
        "lock_sha256": hashlib.sha256(lock).hexdigest(),
        "docker_base": BASE,
        "hash_locked_wheels": all(
            " --hash=sha256:" in line and len(line.split(" --hash=sha256:")[-1]) == 64
            for line in lock.decode("utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ),
        "supply_chain_vulnerability_scan_passed": False,
        "real_cloudflare_verified": False,
        "production_deployed": False,
    }


def installed_versions_match(lock_path: Path) -> bool:
    expected = parse_lock(lock_path.read_text(encoding="utf-8"))
    mismatches = [
        name for name, version in expected.items()
        if metadata.version(name) != version
    ]
    if mismatches:
        raise ValueError("INSTALLED_PACKAGE_VERSION_DRIFT:" + ",".join(mismatches))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--inside-runtime", action="store_true")
    args = ap.parse_args()
    if args.inside_runtime:
        installed_versions_match(Path(args.root) / "requirements.lock")
        print(json.dumps({"package_lock_exact_match": True}, sort_keys=True))
        return 0
    report = inspect(Path(args.root))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
