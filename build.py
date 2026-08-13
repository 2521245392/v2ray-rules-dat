#!/usr/bin/env python3
"""Build a minimal geosite.dat containing only the requested seven lists."""

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
SOURCE_BASE = (
    "https://raw.githubusercontent.com/"
    "Loyalsoldier/v2ray-rules-dat/release"
)
COMPILER_REPOSITORY = "https://github.com/Loyalsoldier/domain-list-custom.git"
COMPILER_REF = "efacb51b8950ae673ebb6dcb9e7ecdd1decb1b6d"
CATEGORIES = (
    "china-list",
    "apple-cn",
    "google-cn",
    "gfw",
    "win-spy",
    "win-update",
    "win-extra",
)


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def download(url: str, destination: Path) -> int:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "custom-geosite-builder/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    if not payload.strip():
        raise RuntimeError(f"Downloaded an empty rule list: {url}")
    destination.write_bytes(payload)
    return sum(1 for line in payload.splitlines() if line.strip())


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

    counts: dict[str, int] = {}
    urls: dict[str, str] = {}

    with tempfile.TemporaryDirectory(prefix="custom-geosite-") as temporary:
        temporary_path = Path(temporary)
        data_path = temporary_path / "data"
        compiler_path = temporary_path / "compiler"
        compiler_output = temporary_path / "compiler-output"
        data_path.mkdir()

        for category in CATEGORIES:
            url = f"{SOURCE_BASE}/{category}.txt"
            print(f"Downloading {category}: {url}", flush=True)
            counts[category] = download(url, data_path / category)
            urls[category] = url

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
            {"name": category, "source": urls[category], "source_lines": counts[category]}
            for category in CATEGORIES
        ],
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
