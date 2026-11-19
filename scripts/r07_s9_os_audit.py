"""S9: OS package CycloneDX manifest and fail-closed Trivy JSON result checker.

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
    if not isinstance(scan, dict):
        raise ValueError("OS_SCAN_MISSING")
    if scan.get("ArtifactType") != "container_image":
        raise ValueError("OS_SCAN_WRONG_ARTIFACT")
    results = scan.get("Results")
    if not isinstance(results, list):
        raise ValueError("OS_SCAN_INCOMPLETE")
    os_results = [r for r in results if isinstance(r, dict)
                  and r.get("Class") == "os-pkgs"]
    if not os_results:
        raise ValueError("OS_SCAN_NO_OS_COVERAGE")
    findings = []
    for result in os_results:
        for vuln in result.get("Vulnerabilities") or []:
            if not isinstance(vuln, dict) or not isinstance(vuln.get("VulnerabilityID"), str):
                raise ValueError("OS_SCAN_INVALID_VULNERABILITY")
            severity = vuln.get("Severity", "UNKNOWN")
            if severity in {"HIGH", "CRITICAL", "UNKNOWN"}:
                findings.append({
                    "id": vuln["VulnerabilityID"], "severity": severity,
                    "package": vuln.get("PkgName", "unknown"),
                    "installed_version": vuln.get("InstalledVersion", ""),
                    "fixed_version": vuln.get("FixedVersion", ""),
                })
    return {
        "os_scope_present": True,
        "os_critical_high_unknown_findings": findings,
        "os_blocking_findings": len(findings),
        "ready_for_supply_chain_gate": len(findings) == 0,
        "runtime_deployed": False,
        "production_homologated": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpkg-list", default="")
    ap.add_argument("--sbom-out", default="")
    ap.add_argument("--scan-json", default="")
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
    if args.scan_json:
        scan = json.loads(Path(args.scan_json).read_text(encoding="utf-8"))
        report.update(inspect_os_scan(scan))
    if not report:
        raise ValueError("NO_OS_INPUT")
    print(json.dumps(report, sort_keys=True))
    return 1 if report.get("ready_for_supply_chain_gate") is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
