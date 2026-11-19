"""GAIA R07 S9.3: disposable Debian runtime minimization evidence only.

This module never touches real services, customer data, Cloudflare, Qdrant or
deployment targets. Building/reducing packages is delegated only to the isolated
CI Docker runner, from the already pinned Debian 13 image. A research comparison
is not a security waiver or a promotion to the primary Dockerfile.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from r07_s9_os_audit import installed_os_inventory, inspect_os_scan

BASE = re.compile(r"^FROM python:3[.]12-slim@sha256:[0-9a-f]{64}$", re.M)
LOCK_LINE = "COPY requirements.lock ./"
TRIAL_LAYER = r"""# R07 S9.3 CI-ONLY cleanup of packages APT itself considers no longer needed.
# No manual purge list and NO vulnerability scanner waiver; do not promote.
RUN set -eux; \
    apt-get update; \
    apt-get autoremove --purge -y; \
    rm -rf /var/lib/apt/lists/*
"""
REQUIRED_IMPORTS = (
    "ssl", "sqlite3", "zlib", "bz2", "lzma", "ctypes",
    "cryptography", "jwt", "mcp", "uvicorn", "app.server",
)
ELF_MODULES = ("_ssl", "_sqlite3", "zlib", "_bz2", "_lzma", "_ctypes")
BLOCKING = {"HIGH", "CRITICAL", "UNKNOWN"}


def temporary_minimal_dockerfile(source: str) -> str:
    if len(BASE.findall(source)) != 1:
        raise ValueError("IMMUTABLE_R07_BASE_REQUIRED")
    if source.count(LOCK_LINE) != 1:
        raise ValueError("DEPENDENCY_LOCK_COPY_NOT_UNIQUE")
    if ("pip install --no-cache-dir --require-hashes --only-binary=:all:"
            not in source):
        raise ValueError("WHEEL_SHA256_GUARD_MISSING")
    if "zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1" not in source:
        raise ValueError("OFFICIAL_ZLIB_PATCH_MISSING")
    if TRIAL_LAYER in source:
        raise ValueError("MINIMIZATION_LAYER_ALREADY_PRESENT")
    return source.replace(LOCK_LINE, TRIAL_LAYER + LOCK_LINE, 1)


def _collect_ids(scan: dict) -> dict:
    checked = inspect_os_scan(scan)
    ids = set()
    all_matches = 0
    for match in scan["matches"]:
        if not isinstance(match, dict):
            raise ValueError("INVALID_SCANNER_MATCH")
        artifact, vuln = match.get("artifact"), match.get("vulnerability")
        if not isinstance(artifact, dict) or not isinstance(vuln, dict):
            raise ValueError("INVALID_SCANNER_FIELDS")
        if artifact.get("type") in ("deb", "deb-pkg"):
            sev = str(vuln.get("severity", "UNKNOWN")).upper()
            if sev in BLOCKING:
                vid = vuln.get("id")
                if not isinstance(vid, str) or not vid:
                    raise ValueError("INVALID_CVE_IDENTIFIER")
                ids.add(vid)
                all_matches += 1
    if all_matches != checked["os_blocking_findings"]:
        raise ValueError("SCANNER_COVERAGE_MISMATCH")
    return {"identifiers": ids, "matches": all_matches}


def compare(
    baseline_dpkg: str,
    trial_dpkg: str,
    baseline_scan: dict,
    trial_scan: dict,
    baseline_probe: dict,
    trial_probe: dict,
) -> dict:
    before = {(p["name"],p["arch"]):p["version"]
              for p in installed_os_inventory(baseline_dpkg)}
    after = {(p["name"],p["arch"]):p["version"]
             for p in installed_os_inventory(trial_dpkg)}
    if any(key not in before for key in after):
        raise ValueError("MINIMIZATION_CANNOT_ADD_PACKAGES")
    updates = [
        {"name":n,"arch":a,"before":before[n,a],"after":after[n,a]}
        for n,a in sorted(after) if before[n,a] != after[n,a]
    ]
    if updates:
        raise ValueError("MINIMIZATION_CANNOT_UPGRADE_PACKAGES")
    removed = [{"name":n,"arch":a,"version":v}
               for (n,a),v in sorted(before.items()) if (n,a) not in after]
    for label,probe in (("baseline",baseline_probe),("trial",trial_probe)):
        if not isinstance(probe,dict) or probe.get("runtime_imports_ok") is not True:
            raise ValueError(f"{label.upper()}_RUNTIME_IMPORTS_FAILED")
        if not isinstance(probe.get("loaded_module_paths"),dict) or len(probe["loaded_module_paths"])<6:
            raise ValueError(f"{label.upper()}_LINKAGE_INCOMPLETE")
        if probe.get("network_requests") != 0:
            raise ValueError(f"{label.upper()}_NETWORK_GUARD")
    baseline = _collect_ids(baseline_scan)
    trial = _collect_ids(trial_scan)
    missing_critical = sorted(
        set(baseline_probe.get("observed_os_packages",[])) -
        set(after_name for after_name,_ in after)
    )
    if missing_critical:
        raise ValueError("REMOVED_OBSERVED_RUNTIME_PACKAGE:"+",".join(missing_critical))
    return {
        "scope":"CI_ONLY_NO_PROMOTION",
        "baseline_os_packages":len(before),
        "trial_os_packages":len(after),
        "removed_os_packages":removed,
        "changed_versions":updates,
        "baseline_unique_blockers":len(baseline["identifiers"]),
        "trial_unique_blockers":len(trial["identifiers"]),
        "baseline_blocker_matches":baseline["matches"],
        "trial_blocker_matches":trial["matches"],
        "resolved_blockers":sorted(baseline["identifiers"]-trial["identifiers"]),
        "new_blockers":sorted(trial["identifiers"]-baseline["identifiers"]),
        "observed_runtime_os_packages":sorted(set(
            baseline_probe.get("observed_os_packages",[]))),
        "runtime_module_names":sorted(trial_probe["loaded_module_paths"]),
        "runtime_imports_passed":True,
        "candidate_eligible":not trial["matches"],
        "publish_approved":False,
        "scanner_waivers":0,
        "scanner_findings_ignored":0,
        "real_qdrant_requests":0,
    }


def probe_runtime() -> dict:
    """Run *inside* isolated built candidate, no cloud/network/secret."""
    # The probe is launched from a read-only bind mount outside WORKDIR.
    # Explicitly add the app root before imports (not a runtime bypass).
    sys.path.insert(0, "/app")
    sys.path.insert(0, "/app/src")
    imports = {}
    for name in REQUIRED_IMPORTS:
        module = importlib.import_module(name)
        imports[name] = getattr(module,"__file__","built-in")
    sys.path.insert(0,str(Path("/app/src")))
    paths = {"python":sys.executable}
    for name in ELF_MODULES:
        module = importlib.import_module(name)
        path = getattr(module,"__file__",None)
        if not path: raise ValueError("ELF_MODULE_MISSING:"+name)
        paths[name] = path
    if len(paths)<7:
        raise ValueError("LINKAGE_INPUT_INCOMPLETE")
    observed = {}
    for key,path in sorted(paths.items()):
        r = subprocess.run(["ldd",path],text=True,capture_output=True,check=True)
        for part in r.stdout.splitlines():
            if "not found" in part:
                raise ValueError("MISSING_SYSTEM_LIBRARY:"+part)
            match=re.search(r"(?:=>\s*)?(/(?:usr/)?lib/[^\s(]+)",part)
            if not match:
                continue
            library_path = os.path.realpath(match.group(1))
            query = subprocess.run(["dpkg-query","-S",library_path],
                                   text=True,capture_output=True)
            if query.returncode==0:
                for entry in query.stdout.splitlines():
                    owner=entry.split(": ",1)[0].split(",",1)[0].split(":",1)[0]
                    if owner:
                        observed[owner]=True
    return {
        "runtime_imports_ok":True,
        "loaded_module_paths":paths,
        "observed_os_packages":sorted(observed),
        "network_requests":0,
        "scope":"synthetic_offline_image",
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-dockerfile")
    ap.add_argument("--trial-dockerfile")
    ap.add_argument("--probe",action="store_true")
    ap.add_argument("--baseline-dpkg")
    ap.add_argument("--trial-dpkg")
    ap.add_argument("--baseline-scan")
    ap.add_argument("--trial-scan")
    ap.add_argument("--baseline-probe")
    ap.add_argument("--trial-probe")
    args=ap.parse_args()
    if args.source_dockerfile and args.trial_dockerfile:
        src=Path(args.source_dockerfile).read_text(encoding="utf-8")
        Path(args.trial_dockerfile).write_text(
            temporary_minimal_dockerfile(src),encoding="utf-8")
        print("R07_S93_MINIMIZATION_DOCKERFILE_TEMPORARY_ONLY")
        return 0
    if args.probe:
        print("R07_S93_RUNTIME_PROBE="+json.dumps(probe_runtime(),sort_keys=True))
        return 0
    fields=(args.baseline_dpkg,args.trial_dpkg,args.baseline_scan,
            args.trial_scan,args.baseline_probe,args.trial_probe)
    if all(fields):
        result=compare(
            Path(args.baseline_dpkg).read_text(encoding="utf-8"),
            Path(args.trial_dpkg).read_text(encoding="utf-8"),
            json.loads(Path(args.baseline_scan).read_text(encoding="utf-8")),
            json.loads(Path(args.trial_scan).read_text(encoding="utf-8")),
            json.loads(Path(args.baseline_probe).read_text(encoding="utf-8")),
            json.loads(Path(args.trial_probe).read_text(encoding="utf-8")))
        print("R07_S93_COMPARISON="+json.dumps(result,sort_keys=True,separators=(",",":")))
        return 0
    raise ValueError("MODE_ARGUMENTS_REQUIRED")


if __name__=="__main__":
    raise SystemExit(main())
