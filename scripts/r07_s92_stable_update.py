"""R07 S9.2: candidate-only stable Debian upgrade and Grype comparison.

Only creates a disposable Dockerfile and consumes synthetic/local public scan
results. Never writes to production or declares CI comparison a security GO.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from r07_s9_os_audit import installed_os_inventory, inspect_os_scan

_BASE = re.compile(r"^FROM python:3\.12-slim@sha256:[a-f0-9]{64}$", re.M)
_ANCHOR = "COPY requirements.lock ./"
_UPGRADE = r"""# S9.2 CI-only official Debian 13 stable/security upgrade trial.
# Base distro unchanged; no sid/forky/testing and no scanner waiver.
RUN set -eux; \
    suites="$(grep -RhE '^(Suites:|deb )' /etc/apt/sources.list.d /etc/apt/sources.list 2>/dev/null || true)"; \
    printf '%s\n' "$suites" | grep -q 'trixie'; \
    if printf '%s\n' "$suites" | grep -Eiq '(^|[^a-z])(sid|forky|unstable|testing|bookworm)([^a-z]|$)'; then exit 94; fi; \
    apt-get update; \
    apt-get upgrade -y --no-install-recommends; \
    rm -rf /var/lib/apt/lists/*
"""


def trial_dockerfile(text: str) -> str:
    if len(_BASE.findall(text)) != 1 or text.count(_ANCHOR) != 1:
        raise ValueError("BASE_OR_LOCK_ANCHOR_INVALID")
    if "--require-hashes --only-binary=:all:" not in text:
        raise ValueError("WHEEL_HASH_POLICY_MISSING")
    if "zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1" not in text:
        raise ValueError("S91_SECURITY_PATCH_MISSING")
    if "sid" in text.lower().split("FROM ", 1)[0]:
        raise ValueError("UNEXPECTED_DOCKER_PREAMBLE")
    return text.replace(_ANCHOR, _UPGRADE + _ANCHOR, 1)


def _blocking_cves(scan: dict) -> set[str]:
    result = inspect_os_scan(scan)
    if result["scanner"] != "grype" or result["os_scope_present"] is not True:
        raise ValueError("AUDIT_COVERAGE_MISSING")
    return {str(x["id"]) for x in result["os_blocking_details"]}


def compare(
    before_scan: dict,
    after_scan: dict,
    before_dpkg: str,
    after_dpkg: str,
) -> dict:
    before = inspect_os_scan(before_scan)
    after = inspect_os_scan(after_scan)
    base_ids, trial_ids = _blocking_cves(before_scan), _blocking_cves(after_scan)
    original = {(p["name"], p["arch"]): p["version"]
                for p in installed_os_inventory(before_dpkg)}
    trial = {(p["name"], p["arch"]): p["version"]
             for p in installed_os_inventory(after_dpkg)}
    # Keep a full inventory, not merely a curated list of vulnerable packages.
    changes = [
        {"name": name, "arch": arch, "from": old, "to": trial.get((name, arch))}
        for (name, arch), old in sorted(original.items())
        if trial.get((name, arch)) != old
    ]
    additions = [
        {"name": name, "arch": arch, "version": version}
        for (name, arch), version in sorted(trial.items())
        if (name, arch) not in original
    ]
    findings = {
        "method": "CI stable-debian-13-upgrade-only",
        "baseline_packages": len(original),
        "trial_packages": len(trial),
        "updated_or_removed_packages": changes,
        "added_packages": additions,
        "baseline_unique_blocking_ids": len(base_ids),
        "trial_unique_blocking_ids": len(trial_ids),
        "baseline_blocking_matches": before["os_blocking_findings"],
        "trial_blocking_matches": after["os_blocking_findings"],
        "removed_blocking_ids": sorted(base_ids - trial_ids),
        "new_blocking_ids": sorted(trial_ids - base_ids),
        "baseline_severity_counts": before["os_severity_counts"],
        "trial_severity_counts": after["os_severity_counts"],
        "candidate_eligible": after["ready_for_supply_chain_gate"],
        "improvement_without_new_blockers": (
            bool(base_ids - trial_ids) and not (trial_ids - base_ids)
        ),
        "promote_automatically": False,
        "production_homologated": False,
        "scanner_waivers": 0,
        "real_services_accessed": False,
    }
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dockerfile", default="")
    ap.add_argument("--write-trial", default="")
    ap.add_argument("--before-scan", default="")
    ap.add_argument("--after-scan", default="")
    ap.add_argument("--before-dpkg", default="")
    ap.add_argument("--after-dpkg", default="")
    args = ap.parse_args()
    if args.dockerfile and args.write_trial:
        result = trial_dockerfile(Path(args.dockerfile).read_text(encoding="utf-8"))
        Path(args.write_trial).write_text(result, encoding="utf-8")
        print("S92_TRIAL_DOCKERFILE_OFFICIAL_STABLE_ONLY=true")
        return 0
    if all((args.before_scan, args.after_scan, args.before_dpkg, args.after_dpkg)):
        result = compare(
            json.loads(Path(args.before_scan).read_text(encoding="utf-8")),
            json.loads(Path(args.after_scan).read_text(encoding="utf-8")),
            Path(args.before_dpkg).read_text(encoding="utf-8"),
            Path(args.after_dpkg).read_text(encoding="utf-8"),
        )
        print("S92_STABLE_COMPARISON=" + json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        # This is research, not a promotion gate. The existing Grype OS job
        # continues to fail whenever it finds HIGH/CRITICAL/UNKNOWN findings.
        return 0
    raise ValueError("COMPLETE_MODE_ARGUMENTS_REQUIRED")


if __name__ == "__main__":
    raise SystemExit(main())
