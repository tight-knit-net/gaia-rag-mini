"""S9.1: compare supported immutable-digest Python/Debian candidate images.

Pure parser: sees only local Grype JSON plus the image digest supplied by an
ephemeral GitHub runner. No network or real infrastructure. A comparison job
may succeed as RESEARCH when candidate_eligible=False; it MUST NOT replace
the original fail-closed promotion job or authorize any production operation.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from r07_s9_os_audit import inspect_os_scan

PINNED = re.compile(r"^(?:docker\.io/library/)?python@sha256:[a-f0-9]{64}$")
SEVERITIES = {"CRITICAL", "HIGH", "UNKNOWN"}


def compare(report: dict, image_ref: str, variant: str) -> dict:
    if not isinstance(image_ref, str) or not PINNED.fullmatch(image_ref):
        raise ValueError("IMMUTABLE_PYTHON_IMAGE_DIGEST_REQUIRED")
    if variant not in {"slim-bookworm", "slim-trixie"}:
        raise ValueError("UNSUPPORTED_BASE_VARIANT")
    outcome = inspect_os_scan(report)
    if not outcome["os_scope_present"] or outcome["scanner"] != "grype":
        raise ValueError("SCANNER_COVERAGE_MISSING")
    blocked = defaultdict(lambda: {"packages": set(), "fix_versions": set()})
    for match in report["matches"]:
        if not isinstance(match, dict) or not isinstance(match.get("artifact"), dict):
            raise ValueError("SCAN_MATCH_INVALID")
        artifact, vuln = match["artifact"], match.get("vulnerability")
        if artifact.get("type") not in {"deb", "deb-pkg"}:
            continue
        if not isinstance(vuln, dict):
            raise ValueError("SCAN_VULNERABILITY_INVALID")
        severity = str(vuln.get("severity", "UNKNOWN")).upper()
        if severity not in SEVERITIES:
            continue
        ident = vuln.get("id")
        if not isinstance(ident, str) or not ident:
            raise ValueError("SCAN_CVE_ID_MISSING")
        blocked[ident]["packages"].add(str(artifact.get("name", "")))
        fix = vuln.get("fix")
        if isinstance(fix, dict):
            for version in fix.get("versions") or []:
                if isinstance(version, str) and version not in {"(won't fix)", "none"}:
                    blocked[ident]["fix_versions"].add(version)
    cves = [{
        "id": ident,
        "packages": sorted(v["packages"]),
        "scanner_fix_versions": sorted(v["fix_versions"]),
        "official_debian_tracker": f"https://security-tracker.debian.org/tracker/{ident}"
    } for ident, v in sorted(blocked.items())]
    return {
        "variant": variant,
        "image_ref": image_ref,
        "os_severity_counts": outcome["os_severity_counts"],
        "os_blocking_matches": outcome["os_blocking_findings"],
        "unique_blocking_cves": len(cves),
        "cves": cves,
        "candidate_eligible": outcome["ready_for_supply_chain_gate"],
        "CI_comparison_only": True,
        "wheel_hash_change_authorized": False,
        "ignore_rules_used": False,
        "production_deployed": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--variant", required=True)
    args = ap.parse_args()
    result = compare(json.loads(Path(args.report).read_text(encoding="utf-8")),
                     args.image, args.variant)
    print("R07_S91_COMPARISON=" + json.dumps(result, ensure_ascii=False,
                                          separators=(",", ":"), sort_keys=True))
    # The comparison step is NOT a security acceptance step: old hard
    # blocking OS scan and candidate acceptance stay unchanged.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
