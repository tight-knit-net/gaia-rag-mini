"""R07 S8 deterministic CycloneDX SBOM and fail-closed public PyPI advisory gate.

The SBOM enumerates the 29 pinned R07 Python distributions, NOT actual wheel
hashes, OS packages, the Docker image, host code or production provenance.
The audit input/output references only PUBLIC package names and versions.
No external network access is made by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
from pathlib import Path

from r07_s7_package_preflight import parse_lock

SCHEMA = "https://cyclonedx.org/schema/bom-1.6.schema.json"
APP = "pkg:generic/gaia-rag-mini@r07-candidate"


def create_sbom(lock_bytes: bytes) -> dict:
    requirements = parse_lock(lock_bytes.decode("utf-8"))
    digest = hashlib.sha256(lock_bytes).hexdigest()
    components = [
        {
            "type": "library",
            "name": name,
            "version": version,
            "purl": f"pkg:pypi/{name}@{version}",
            "bom-ref": f"pkg:pypi/{name}@{version}",
            "scope": "required",
        }
        for name, version in sorted(requirements.items())
    ]
    return {
        "$schema": SCHEMA,
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, digest)),
        "version": 1,
        "metadata": {
            "component": {
                "type": "application", "name": "gaia-rag-mini-r07",
                "version": "0.7.0-candidate", "bom-ref": APP,
                "properties": [
                    {"name": "gaia:requirements-lock-sha256", "value": digest},
                    {"name": "gaia:scope", "value": "python-lock-only"},
                ],
            },
        },
        "components": components,
        "dependencies": [{
            "ref": APP, "dependsOn": [x["bom-ref"] for x in components],
        }],
    }


def validate_sbom(bom: dict, lock_bytes: bytes) -> dict:
    expected = create_sbom(lock_bytes)
    if bom != expected:
        raise ValueError("SBOM_DRIFT_FROM_LOCK")
    return {
        "sbom_spec_version": "1.6",
        "python_components": len(expected["components"]),
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "sbom_reproducible": True,
        "wheel_hashes_verified": False,
        "base_image_os_components_included": False,
    }


def validate_public_audit(payload: dict, lock_bytes: bytes) -> dict:
    """Reject incomplete/skipped audits; never interpret unknown as clean."""
    expected = parse_lock(lock_bytes.decode("utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("dependencies"), list):
        raise ValueError("ADVISORY_AUDIT_INVALID")
    rows = payload["dependencies"]
    if len(rows) != len(expected):
        raise ValueError("ADVISORY_AUDIT_INCOMPLETE")
    seen: set[str] = set()
    vulnerabilities = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("ADVISORY_AUDIT_INVALID_ROW")
        name = item.get("name")
        version = item.get("version")
        if not isinstance(name, str):
            raise ValueError("ADVISORY_AUDIT_INVALID_NAME")
        normalized = re.sub("[-_.]+", "-", name).lower()
        if normalized in seen or expected.get(normalized) != version:
            raise ValueError("ADVISORY_AUDIT_VERSION_OR_DUPLICATE")
        seen.add(normalized)
        issues = item.get("vulns")
        if not isinstance(issues, list):
            raise ValueError("ADVISORY_AUDIT_MISSING_VULNS")
        for issue in issues:
            if not isinstance(issue, dict) or not isinstance(issue.get("id"), str):
                raise ValueError("ADVISORY_AUDIT_UNSTRUCTURED_FINDING")
            vulnerabilities.append({
                "package": normalized, "version": version,
                "vulnerability_id": issue["id"],
                "fix_versions": [v for v in issue.get("fix_versions", [])
                                 if isinstance(v, str)][:8],
            })
    if seen != set(expected):
        raise ValueError("ADVISORY_AUDIT_MISSING_PACKAGE")
    report = {
        "scanner_input": "public_python_package_names_and_versions_only",
        "analyzed_count": len(seen),
        "vulnerability_count": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
        "clean": len(vulnerabilities) == 0,
        "external_risk_feed_used_by_ci": True,
        "scan_scope": "Python PyPI advisories; not OS, containers, secrets or zero-day",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", default="requirements.lock")
    parser.add_argument("--sbom-out", default="")
    parser.add_argument("--verify-sbom", default="")
    parser.add_argument("--audit-report", default="")
    args = parser.parse_args()
    lock_bytes = Path(args.lock).read_bytes()
    sbom = create_sbom(lock_bytes)
    report = validate_sbom(sbom, lock_bytes)
    if args.sbom_out:
        Path(args.sbom_out).write_text(
            json.dumps(sbom, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.verify_sbom:
        stored = json.loads(Path(args.verify_sbom).read_text(encoding="utf-8"))
        report.update(validate_sbom(stored, lock_bytes))
    if args.audit_report:
        findings = json.loads(Path(args.audit_report).read_text(encoding="utf-8"))
        audited = validate_public_audit(findings, lock_bytes)
        report.update(audited)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 1 if report.get("clean") is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
