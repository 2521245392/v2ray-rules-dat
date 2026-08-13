#!/usr/bin/env python3
"""Build a personal geosite.dat tailored to the accompanying routing rules."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COMPILER_REPOSITORY = "https://github.com/Loyalsoldier/domain-list-custom.git"
COMPILER_REF = "efacb51b8950ae673ebb6dcb9e7ecdd1decb1b6d"
CATEGORIES = ("private", "cn", "gfw")
REQUIRED_RULES = (
    "private=localhost",
    "cn=qq.com",
    "cn=a1.mzstatic.com",
    "cn=265.com",
    "gfw=youtube.com",
)
DIRECT_TLD_SOURCE = (
    "https://raw.githubusercontent.com/"
    "Loyalsoldier/v2ray-rules-dat/release/direct-tld-list.txt"
)
SOURCE_COMPONENTS = {
    "private": (
        (
            "v2fly-private",
            "https://raw.githubusercontent.com/"
            "v2fly/domain-list-community/master/data/private",
        ),
    ),
    # This personal CN category folds known-direct domains, Apple China and
    # Google China into one target. Bare TLD rules are explicitly filtered.
    "cn": (
        (
            "direct-list",
            "https://raw.githubusercontent.com/"
            "Loyalsoldier/v2ray-rules-dat/release/direct-list.txt",
        ),
        (
            "apple-cn",
            "https://raw.githubusercontent.com/"
            "Loyalsoldier/v2ray-rules-dat/release/apple-cn.txt",
        ),
        (
            "google-cn",
            "https://raw.githubusercontent.com/"
            "Loyalsoldier/v2ray-rules-dat/release/google-cn.txt",
        ),
    ),
    "gfw": (
        (
            "gfw",
            "https://raw.githubusercontent.com/"
            "Loyalsoldier/v2ray-rules-dat/release/gfw.txt",
        ),
    ),
}


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def download(url: str) -> tuple[bytes, int]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "custom-geosite-builder/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    if not payload.strip():
        raise RuntimeError(f"Downloaded an empty rule list: {url}")
    return payload, sum(1 for line in payload.splitlines() if line.strip())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command was not found: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist",
        help="Output directory (default: ./dist)",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    require_command("git")
    require_command("go")

    source_manifest: dict[str, list[dict[str, str | int]]] = {}
    filters: list[dict[str, str | int]] = []

    with tempfile.TemporaryDirectory(prefix="custom-geosite-") as temporary:
        temporary_path = Path(temporary)
        data_path = temporary_path / "data"
        compiler_path = temporary_path / "compiler"
        compiler_output = temporary_path / "compiler-output"
        data_path.mkdir()

        print(f"Downloading CN TLD exclusion list: {DIRECT_TLD_SOURCE}", flush=True)
        tld_payload, tld_line_count = download(DIRECT_TLD_SOURCE)
        excluded_tlds = {
            line.strip().lower()
            for line in tld_payload.splitlines()
            if line.strip() and not line.lstrip().startswith(b"#")
        }
        forbidden_rules = tuple(
            f"cn={rule.decode('ascii')}" for rule in sorted(excluded_tlds)
        )

        for category in CATEGORIES:
            destination = data_path / category
            source_manifest[category] = []
            with destination.open("wb") as output_file:
                for component, url in SOURCE_COMPONENTS[category]:
                    print(f"Downloading {category}/{component}: {url}", flush=True)
                    payload, line_count = download(url)
                    removed_count = 0
                    if category == "cn" and component == "direct-list":
                        original_lines = payload.splitlines()
                        filtered_lines = [
                            line
                            for line in original_lines
                            if line.strip().lower() not in excluded_tlds
                        ]
                        removed_count = len(original_lines) - len(filtered_lines)
                        payload = b"\n".join(filtered_lines) + b"\n"
                    output_file.write(payload)
                    if not payload.endswith(b"\n"):
                        output_file.write(b"\n")
                    source_manifest[category].append(
                        {
                            "component": component,
                            "source": url,
                            "source_lines": line_count,
                            "output_lines": sum(
                                1 for line in payload.splitlines() if line.strip()
                            ),
                            "excluded_rules": removed_count,
                        }
                    )
        filters.append(
            {
                "target": "cn/direct-list",
                "action": "remove exact bare TLD rules",
                "source": DIRECT_TLD_SOURCE,
                "source_lines": tld_line_count,
                "removed_rules": len(excluded_tlds),
            }
        )

        run(["git", "clone", "--no-checkout", COMPILER_REPOSITORY, str(compiler_path)])
        run(["git", "checkout", COMPILER_REF], cwd=compiler_path)
        run(
            [
                "go",
                "run",
                ".",
                f"--datapath={data_path}",
                f"--outputpath={compiler_output}",
                "--exportlists=",
                "--togfwlist=",
                "--excludeattrs=",
            ],
            cwd=compiler_path,
        )

        generated = compiler_output / "geosite.dat"
        if not generated.is_file() or generated.stat().st_size == 0:
            raise RuntimeError("Compiler did not produce a valid geosite.dat")

        destination = output / "geosite.dat"
        shutil.copyfile(generated, destination)

    verifier_path = ROOT / "tools" / "verify"
    run(
        [
            "go",
            "run",
            ".",
            f"--file={output / 'geosite.dat'}",
            f"--expect={','.join(CATEGORIES)}",
            f"--require={','.join(REQUIRED_RULES)}",
            f"--forbid={','.join(forbidden_rules)}",
        ],
        cwd=verifier_path,
    )

    dat_path = output / "geosite.dat"
    digest = sha256(dat_path)
    (output / "geosite.dat.sha256sum").write_text(
        f"{digest}  geosite.dat\n", encoding="utf-8", newline="\n"
    )
    manifest = {
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "compiler": {
            "repository": COMPILER_REPOSITORY,
            "commit": COMPILER_REF,
        },
        "artifact": {
            "name": "geosite.dat",
            "size": dat_path.stat().st_size,
            "sha256": digest,
        },
        "categories": [
            {"name": category, "sources": source_manifest[category]}
            for category in CATEGORIES
        ],
        "filters": filters,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Built {dat_path} ({dat_path.stat().st_size} bytes)")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
