"""S9: OS package CycloneDX manifest and fail-closed Grype JSON result checker.

Only Linux/Debian installed system package names and versions. No Docker
socket, network access, secrets, user content or snapshot writes by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

_NAME = re.compile(r"^[a-z0-9][a-z0-9+.-]{0,120}$")
_ARCH = re.compile(r"^[a-zA-Z0-9_-]{2,32}$")


def installed_os_inventory(text: str) -> list[dict]:
    packages = {}
    for line in text.splitlines():
        columns = line.split("\t")
        if len(columns) != 3:
            raise ValueError("MALFORMED_DPKG_INVENTORY")
        name, version, arch = columns
        if not (_NAME.fullmatch(name) and 1 <= len(version) <= 120
                and not any(c.isspace() for c in version)
                and _ARCH.fullmatch(arch)):
            raise ValueError("INVALID_OS_PACKAGE")
        key = (name, arch)
        if key in packages:
            raise ValueError("DUPLICATE_OS_PACKAGE")
        packages[key] = version
    if len(packages) < 20:
        raise ValueError("INCOMPLETE_OS_PACKAGE_INVENTORY")
    return [
        {"name": name, "version": packages[name, arch], "arch": arch}
        for name, arch in sorted(packages)
    ]


def build_os_sbom(text: str) -> dict:
    entries = installed_os_inventory(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    components = []
    for item in entries:
        purl = (f"pkg:deb/debian/{item['name']}@{item['version']}"
                f"?arch={item['arch']}")
        components.append({
            "type": "operating-system",
            "name": item["name"],
            "version": item["version"],
            "purl": purl,
            "bom-ref": purl,
        })
    return {
        "bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
        "metadata": {"component": {
            "type": "container", "name": "gaia-rag-mini-r07",
            "version": "s9-disposable-image",
            "properties": [
                {"name": "gaia:inventory-sha256", "value": digest},
                {"name": "gaia:coverage", "value": "installed-debian-packages-only"},
            ],
        }},
        "components": components,
    }


def inspect_os_scan(scan: dict) -> dict:
    """Fail closed if Grype reports are absent/invalid/contain blocking OS CVEs."""
    if not isinstance(scan, dict):
        raise ValueError("OS_SCAN_MISSING")
    descriptor = scan.get("descriptor")
    distro = scan.get("distro")
    source = scan.get("source")
    if (not isinstance(descriptor, dict) or descriptor.get("name") != "grype"
            or not isinstance(distro, dict) or distro.get("name") != "debian"
            or not isinstance(source, dict) or source.get("type") != "image"):
        raise ValueError("OS_SCAN_WRONG_ARTIFACT_OR_SCANNER")
    matches = scan.get("matches")
    if not isinstance(matches, list):
        raise ValueError("OS_SCAN_INCOMPLETE")
    findings = []
    counts: dict[str, int] = {}
    for match in matches:
        if not isinstance(match, dict):
            raise ValueError("OS_SCAN_INVALID_MATCH")
        artifact, vuln = match.get("artifact"), match.get("vulnerability")
        if not isinstance(artifact, dict) or not isinstance(vuln, dict):
            raise ValueError("OS_SCAN_INVALID_MATCH")
        if artifact.get("type") not in {"deb", "deb-pkg"}:
            continue
        severity = str(vuln.get("severity", "UNKNOWN")).upper()
        ident = vuln.get("id")
        if not isinstance(ident, str) or not ident:
            raise ValueError("OS_SCAN_INVALID_VULNERABILITY")
        counts[severity] = counts.get(severity, 0) + 1
        if severity in {"HIGH", "CRITICAL", "UNKNOWN"}:
            findings.append({
                "id": ident, "severity": severity,
                "package": artifact.get("name", "unknown"),
                "installed_version": artifact.get("version", ""),
            })
    return {
        "os_scope_present": True,
        "os_severity_counts": counts,
        "os_blocking_findings": len(findings),
        "os_blocking_details": findings[:80],
        "ready_for_supply_chain_gate": len(findings) == 0,
        "scanner": "grype",
        "runtime_deployed": False,
        "production_homologated": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpkg-list", default="")
    ap.add_argument("--sbom-out", default="")
    ap.add_argument("--grype-json", default="")
    args = ap.parse_args()
    report = {}
    if args.dpkg_list:
        bom = build_os_sbom(Path(args.dpkg_list).read_text(encoding="utf-8"))
        report["os_packages"] = len(bom["components"])
        report["os_sbom_type"] = "CycloneDX 1.6 / Debian dpkg only"
        if args.sbom_out:
            Path(args.sbom_out).write_text(
                json.dumps(bom, indent=2, sort_keys=True) + "\n",
                encoding="utf-8")
    if args.grype_json:
        scan = json.loads(Path(args.grype_json).read_text(encoding="utf-8"))
        report.update(inspect_os_scan(scan))
    if not report:
        raise ValueError("NO_OS_INPUT")
    print(json.dumps(report, sort_keys=True))
    return 1 if report.get("ready_for_supply_chain_gate") is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
