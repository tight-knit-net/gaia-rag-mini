"""S9 candidate-only wheel hash lock generator/validator.

Generate from PUBLIC PyPI files on GitHub-hosted Linux x86_64 + Python 3.12
only. No credentials, customers or external services. Bootstrap prints a
base64-encoded public dependency hash lock for controlled GitHub commit;
the CI creates no uploaded artifact or published image.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from pip._vendor.packaging.utils import canonicalize_name, parse_wheel_filename

EXPECTED_COUNT = 29


def parse_pinned(text: str) -> list[tuple[str, str]]:
    from r07_s7_package_preflight import parse_lock
    packages = parse_lock(text)
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        requirement = item.split(" --hash=sha256:")[0].strip()
        name_raw = requirement.split("==", 1)[0].split("[", 1)[0]
        name = canonicalize_name(name_raw)
        if packages.get(name) != requirement.split("==", 1)[-1]:
            raise ValueError("HASH_LOCK_VERSION_INVALID")
        entries.append((requirement, name))
    if len(entries) != EXPECTED_COUNT:
        raise ValueError("WRONG_LOCK_COUNT")
    return entries


def read_hash_lock(text: str) -> dict[str, str]:
    """Require a single explicit hash for each of the installed wheels."""
    import re
    rows = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        hit = re.fullmatch(r"([A-Za-z0-9_.-]+(?:\[crypto\])?==[A-Za-z0-9_.+!-]+)\s+--hash=sha256:([a-f0-9]{64})", s)
        if not hit:
            raise ValueError("UNHASHED_OR_INVALID_REQUIREMENT")
        key = canonicalize_name(hit.group(1).split("==")[0].split("[")[0])
        if key in rows:
            raise ValueError("DUPLICATE_REQUIREMENT")
        rows[key] = hit.group(2)
    if len(rows) != EXPECTED_COUNT:
        raise ValueError("WRONG_LOCK_COUNT")
    return rows


def bootstrap(lock: Path) -> str:
    text = lock.read_text(encoding="utf-8")
    entries = parse_pinned(text)
    with tempfile.TemporaryDirectory(prefix="r07-s9-wheels-") as directory:
        cache = Path(directory)
        subprocess.run([
            sys.executable, "-m", "pip", "download", "--no-deps",
            "--only-binary=:all:", "--disable-pip-version-check",
            "--dest", str(cache), "-r", str(lock),
        ], check=True, stdout=subprocess.DEVNULL)
        wheels = list(cache.glob("*.whl"))
        if len(wheels) != EXPECTED_COUNT:
            raise ValueError("INCOMPLETE_WHEEL_DOWNLOAD")
        seen: dict[str, str] = {}
        for wheel in wheels:
            name, version, _, _ = parse_wheel_filename(wheel.name)
            key = canonicalize_name(str(name))
            if key in seen:
                raise ValueError("DUPLICATE_DOWNLOADED_WHEEL")
            required = next((req for req, name in entries if name == key), None)
            if required is None or str(version) != required.split("==", 1)[1]:
                raise ValueError("DOWNLOADED_WHEEL_MISMATCH")
            seen[key] = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if set(seen) != {name for _, name in entries}:
            raise ValueError("MISSING_WHEEL")
        generated = "\n".join([
            "# GAIA R07 S9 / Python 3.12 / linux-x86_64 / binary wheels only.",
            "# Per-distribution SHA256 from ephemeral GitHub Actions download.",
            "# Deliberately platform-specific; other architectures require a new approved lock.",
            "# Installation must use --require-hashes --only-binary=:all:.",
            *[f"{req} --hash=sha256:{seen[key]}" for req, key in entries],
            "",
        ])
        read_hash_lock(generated)
        hash_file = cache / "requirements.s9-hashed.lock"
        hash_file.write_text(generated, encoding="utf-8")
        subprocess.run([
            sys.executable, "-m", "pip", "download",
            "--no-deps", "--only-binary=:all:", "--no-index",
            "--find-links", str(cache), "--require-hashes",
            "--dest", str(cache / "verified"), "-r", str(hash_file),
        ], check=True, stdout=subprocess.DEVNULL)
        return generated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", default="requirements.lock")
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()
    if args.bootstrap:
        result = bootstrap(Path(args.lock))
        # Public package names/hashes ONLY. No secrets or customer data.
        print("R07_S9_LOCK_SHA256=" + hashlib.sha256(result.encode()).hexdigest())
        print("R07_S9_LOCK_B64=" + base64.b64encode(result.encode()).decode())
    else:
        contents = Path(args.lock).read_text(encoding="utf-8")
        print("R07_S9_HASHED_PACKAGES=" + str(len(read_hash_lock(contents))))


if __name__ == "__main__":
    main()
