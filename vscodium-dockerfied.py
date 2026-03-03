#!/usr/bin/env python3
"""
run.py - single entrypoint to build/run VSCodium docker images.

Encapsulates these scripts from craigphicks/codium-dockerfied:
- build-base.sh
- build-standalone.sh
- build-remoss.sh
- run-standalone.sh
- run-remoss.sh

Usage examples:
  ./run.py build standalone
  ./run.py run standalone
  ./run.py build remoss
  ./run.py run remoss

  # override env.sh values:
  ./run.py build standalone --vscodium-ver 1.109.41146
  ./run.py run remoss --host-workspace ~/github --client-username codium

Notes:
- By default, reads env.sh in the same directory as this script (simple KEY="VALUE" parsing).
- Runs docker commands directly (no shell scripts).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence


ENV_KEYS = {
    "VSCODIUM_VER",
    "HOST_WORKSPACE",
    "CLIENT_USERNAME",
    "HOST_VSCODIUM_CONFIG_DIR",
    "HOST_VSCODIUM_VSCODE_OSS_DIR",
    "REMOSS_REMOTE_NAME",
    "REMOSS_REMOTE_PORT",
    "REMOSS_REMOTE_HOST",
    "VSCODIUM_REH_SERVER_HOST",
    "VSCODIUM_REH_SERVER_PORT",
}


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def run_cmd(cmd: Sequence[str], cwd: Optional[Path] = None, extra_env: Optional[Dict[str, str]] = None) -> None:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    eprint("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True)


def parse_env_sh(env_path: Path) -> Dict[str, str]:
    """
    Minimal parsing for env.sh style lines:
      KEY="value"
      KEY=value
    Ignores comments/blank lines.
    """
    if not env_path.exists():
        raise FileNotFoundError(f"env file not found: {env_path}")

    env: Dict[str, str] = {}
    line_re = re.compile(r"""^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$""")

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = line_re.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)

        # strip inline comments (best-effort)
        if " #" in val:
            val = val.split(" #", 1)[0].strip()

        # strip quotes
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]

        # expand basic ${HOME} and ${VAR}
        def repl(match: re.Match[str]) -> str:
            var = match.group(1)
            return os.environ.get(var, env.get(var, ""))

        val = re.sub(r"\$\{([^}]+)\}", repl, val)
        env[key] = val

    return env


@dataclass
class Config:
    repo_root: Path

    VSCODIUM_VER: str
    HOST_WORKSPACE: str
    CLIENT_USERNAME: str
    HOST_VSCODIUM_CONFIG_DIR: str
    HOST_VSCODIUM_VSCODE_OSS_DIR: str

    WAYLAND_DISPLAY: str
    XDG_RUNTIME_DIR: str
    XAUTHORITY: str

    @staticmethod
    def load(repo_root: Path, args: argparse.Namespace) -> "Config":
        env_path = repo_root / "env.sh"
        file_env = parse_env_sh(env_path)

        def pick(key: str, override: Optional[str] = None, default: Optional[str] = None) -> str:
            if override is not None:
                return override
            if key in file_env:
                return file_env[key]
            if default is not None:
                return default
            raise KeyError(f"Missing required config key {key} (not found in env.sh and no override provided)")

        # pull from OS env if present; otherwise use common defaults
        wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
        xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        xauthority = os.environ.get("XAUTHORITY", str(Path.home() / ".Xauthority"))

        return Config(
            repo_root=repo_root,
            VSCODIUM_VER=pick("VSCODIUM_VER", args.vscodium_ver),
            HOST_WORKSPACE=pick("HOST_WORKSPACE", args.host_workspace),
            CLIENT_USERNAME=pick("CLIENT_USERNAME", args.client_username),
            HOST_VSCODIUM_CONFIG_DIR=pick("HOST_VSCODIUM_CONFIG_DIR", args.host_vscodium_config_dir),
            HOST_VSCODIUM_VSCODE_OSS_DIR=pick("HOST_VSCODIUM_VSCODE_OSS_DIR", args.host_vscodium_vscode_oss_dir),
            WAYLAND_DISPLAY=wayland_display,
            XDG_RUNTIME_DIR=xdg_runtime_dir,
            XAUTHORITY=xauthority,
        )


def image_name(target: str, vscodium_ver: str) -> str:
    return f"vscodium-dockerfied-{target}-{vscodium_ver}.img:latest"


def build(cfg: Config, target: str) -> None:
    """
    target: base | standalone | remoss
    """
    if target == "base":
        workdir = cfg.repo_root / "vscodium-dockerfied-base"
        dockerfile = "Dockerfile.vscodium-dockerfied-base"
        tag = image_name("base", cfg.VSCODIUM_VER)
        cmd = [
            "docker", "build",
            "-f", dockerfile,
            "-t", tag,
            "--build-arg", f"VSCODIUM_VERSION={cfg.VSCODIUM_VER}",
            ".",
        ]
    elif target == "standalone":
        workdir = cfg.repo_root / "vscodium-dockerfied-standalone"
        dockerfile = "Dockerfile.vscodium-dockerfied-standalone"
        tag = image_name("standalone", cfg.VSCODIUM_VER)
        cmd = [
            "docker", "build",
            "-f", dockerfile,
            "-t", tag,
            "--build-arg", f"CLIENT_USERNAME={cfg.CLIENT_USERNAME}",
            "--build-arg", f"VSCODIUM_VER={cfg.VSCODIUM_VER}",
            ".",
        ]
    elif target == "remoss":
        workdir = cfg.repo_root / "vscodium-dockerfied-remoss-client"
        dockerfile = "Dockerfile.vscodium-dockerfied-remoss-client"
        tag = image_name("remoss-client", cfg.VSCODIUM_VER)
        # Note the original script tags "remoss-client" in the image name.
        cmd = [
            "docker", "build",
            "-f", dockerfile,
            "-t", tag,
            "--build-arg", f"CLIENT_USERNAME={cfg.CLIENT_USERNAME}",
            "--build-arg", f"VSCODIUM_VER={cfg.VSCODIUM_VER}",
            ".",
        ]
    else:
        raise ValueError(f"Unknown build target: {target}")

    if not workdir.exists():
        raise FileNotFoundError(f"Expected directory does not exist: {workdir}")

    extra_env = {"DOCKER_BUILDKIT": "1"}
    run_cmd(["ls", "-alt"], cwd=workdir)
    run_cmd(cmd, cwd=workdir, extra_env=extra_env)

    # Show resulting image (like the scripts do)
    run_cmd(["docker", "image", "ls", "--format", "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}"])


def run_container(cfg: Config, mode: str) -> None:
    """
    mode: standalone | remoss
    """
    if mode not in {"standalone", "remoss"}:
        raise ValueError("run mode must be: standalone or remoss")

    if mode == "standalone":
        workdir = cfg.repo_root / "vscodium-dockerfied-standalone"
        container_name = "vscodium-dockerfied-base"  # matches run-standalone.sh
        img = image_name("standalone", cfg.VSCODIUM_VER)
        network_args: list[str] = []
    else:
        workdir = cfg.repo_root / "vscodium-dockerfied-remoss-client"
        container_name = "vscodium-dockerfied-remoss-client"
        img = image_name("remoss-client", cfg.VSCODIUM_VER)
        network_args = ["--network", "host"]

    if not workdir.exists():
        raise FileNotFoundError(f"Expected directory does not exist: {workdir}")

    # Mirrors env/volume usage from run-*.sh
    docker_cmd = [
        "docker", "run", "--rm",
        "--name", container_name,
        *network_args,
        "--shm-size=2gb",
        "-e", "DISPLAY=:0",
        "-e", f"WAYLAND_DISPLAY={cfg.WAYLAND_DISPLAY}",
        "-e", "XDG_RUNTIME_DIR=/tmp/runtime-docker",
        "-e", f"PULSE_SERVER=unix:{cfg.XDG_RUNTIME_DIR}/pulse/native",
        "-e", "XAUTHORITY=/tmp/.Xauthority",
        "-e", "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus",
        "-e", "DOCKER_BUILDKIT=1",
        "-v", f"{cfg.HOST_VSCODIUM_CONFIG_DIR}:/home/{cfg.CLIENT_USERNAME}/.config/VSCodium",
        "-v", f"{cfg.HOST_VSCODIUM_VSCODE_OSS_DIR}:/home/{cfg.CLIENT_USERNAME}/.vscode-oss",
        "-v", "/tmp/.X11-unix:/tmp/.X11-unix",
        "-v", f"{cfg.XAUTHORITY}:/tmp/.Xauthority:ro",
        "-v", f"{cfg.XDG_RUNTIME_DIR}/{cfg.WAYLAND_DISPLAY}:/tmp/runtime-docker/{cfg.WAYLAND_DISPLAY}",
        "-v", f"{cfg.HOST_WORKSPACE}:/workspace",
        "-v", "/run/user/1000/bus:/run/user/1000/bus",
        "-v", f"{cfg.XDG_RUNTIME_DIR}/pulse:/tmp/runtime-docker/pulse",
        img,
    ]

    run_cmd(["ls", "-alt"], cwd=workdir)
    run_cmd(docker_cmd, cwd=workdir)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="run.py")
    sub = p.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build docker image")
    p_build.add_argument("target", choices=["standalone", "remoss", "base"], help="What to build")

    p_run = sub.add_parser("run", help="Run docker image")
    p_run.add_argument("mode", choices=["standalone", "remoss"], help="Which runtime to use")

    # common overrides (read env.sh by default)
    for sp in (p_build, p_run):
        sp.add_argument("--vscodium-ver", dest="vscodium_ver", default=None)
        sp.add_argument("--host-workspace", dest="host_workspace", default=None)
        sp.add_argument("--client-username", dest="client_username", default=None)
        sp.add_argument("--host-vscodium-config-dir", dest="host_vscodium_config_dir", default=None)
        sp.add_argument("--host-vscodium-vscode-oss-dir", dest="host_vscodium_vscode_oss_dir", default=None)

    return p


def main(argv: Sequence[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent
    cfg = Config.load(repo_root, args)

    if args.command == "build":
        build(cfg, args.target)
    elif args.command == "run":
        run_container(cfg, args.mode)
    else:
        parser.error(f"Unknown command: {args.command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))