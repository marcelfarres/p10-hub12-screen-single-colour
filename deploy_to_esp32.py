#!/usr/bin/env python3
"""Deploy the standalone P10 package and demo app to an ESP32 via mpremote."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE_SRC = ROOT / "src" / "p10_hub12_screen"
DEVICE_DEMO = ROOT / "device_demo"


def run_command(command, description, check=True):
    print(description, flush=True)
    return subprocess.run(command, check=check, text=True, capture_output=True)


def detect_device():
    common_ports = ["COM6", "COM5", "COM4", "COM3", "/dev/ttyUSB0", "/dev/ttyACM0"]
    for port in common_ports:
        result = subprocess.run(
            ["uvx", "mpremote", "connect", port, "version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"Detected ESP32 on {port}", flush=True)
            return port
    raise SystemExit("No ESP32 detected. Pass --device <PORT>.")


def ensure_exists(path):
    if not path.exists():
        raise SystemExit(f"Required path not found: {path}")


def copy_file(device, local_path, remote_path):
    result = run_command(
        [
            "uvx",
            "mpremote",
            "connect",
            device,
            "fs",
            "cp",
            str(local_path),
            remote_path,
        ],
        f"Uploading {local_path.name} -> {remote_path}",
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            result.stderr.strip() or f"Failed to copy {local_path} to {remote_path}"
        )


def mkdir(device, remote_path):
    subprocess.run(
        ["uvx", "mpremote", "connect", device, "fs", "mkdir", remote_path],
        capture_output=True,
        text=True,
        check=False,
    )


def deploy_package(device):
    ensure_exists(PACKAGE_SRC)
    mkdir(device, ":lib")
    mkdir(device, ":lib/p10_hub12_screen")

    for path in sorted(PACKAGE_SRC.rglob("*")):
        if path.is_dir() or path.name == "__pycache__":
            continue
        relative = path.relative_to(PACKAGE_SRC).as_posix()
        parent = "/".join(relative.split("/")[:-1])
        if parent:
            mkdir(device, f":lib/p10_hub12_screen/{parent}")
        copy_file(device, path, f":lib/p10_hub12_screen/{relative}")


def deploy_demo(device):
    ensure_exists(DEVICE_DEMO / "main.py")
    ensure_exists(DEVICE_DEMO / "boot.py")
    copy_file(device, DEVICE_DEMO / "boot.py", ":boot.py")
    copy_file(device, DEVICE_DEMO / "main.py", ":main.py")


def reset(device):
    run_command(
        ["uvx", "mpremote", "connect", device, "reset"],
        "Resetting ESP32",
        check=False,
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", help="Serial port, for example COM6")
    parser.add_argument(
        "--no-demo",
        action="store_true",
        help="Only upload the package to /lib and do not replace boot.py or main.py",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if shutil.which("uv") is None:
        raise SystemExit("uv is required on the host path.")

    device = args.device or detect_device()
    deploy_package(device)
    if not args.no_demo:
        deploy_demo(device)
    reset(device)
    print("Standalone P10 package deployment complete.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
