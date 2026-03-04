#!/usr/bin/env python3
"""
vscodium-dockerfied.py

Single entrypoint to build/run VSCodium docker images (standalone or remoss client).

Config search / merge order:
  1) ./conf.json
  2) ~/.config/vscodium-dockerfied/conf.json (overrides #1 if both exist)
  3) CLI overrides everything

Required shell env vars for `run`:
  XDG_RUNTIME_DIR, WAYLAND_DISPLAY, XAUTHORITY
If any are missing, `run` fails with a clear error.

Config format (updated):
{
  "skip_build": false,
  "standalone_args": { "network": "none" },
  "remoss_args": {},
  "docker_build_args": {
    "VSCODIUM_VER": "1.109.41146",
    "CLIENT_USERNAME": "codium"
  },
  "docker_run_args": {
    "HOST_WORKSPACE": "/home/you/github",
    "HOST_VSCODIUM_CONFIG_DIR": "/home/you/.config/VSCodium2",
    "HOST_VSCODIUM_VSCODE_OSS_DIR": "/home/you/.vscode-oss.VSCodium2"
  }
}

Currently supported mode-specific args:
- standalone_args.network: passed as `--network <value>` to docker run (e.g., "none", "host", "bridge")
- remoss_args.network: if set, passed as `--network <value>` (default for remoss is "host" if not provided)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Sequence


REQUIRED_RUN_ENV_VARS = ["XDG_RUNTIME_DIR", "WAYLAND_DISPLAY", "XAUTHORITY"]


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def run_cmd(cmd: Sequence[str], cwd: None | Path = None, extra_env: None | dict[str, str] = None) -> None:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    eprint("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True)


def deep_merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Return new dict = a merged with b, where b overrides a. Nested dicts merge recursively."""
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_json_if_exists(path: Path) -> tuple[Path, dict[str, Any]]:
    if not path.exists():
        return path, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        raise ValueError(f"Invalid JSON in {path}: {ex}") from ex
    if not isinstance(data, dict):
        raise ValueError(f"Config JSON must be an object at top-level: {path}")
    return path, data


def load_config() -> dict[str, Any]:
    """
    Loads config from:
      a) ./conf.json
      b) ~/.config/vscodium-dockerfied/conf.json (overrides a)
    """
    a_path = Path.cwd() / "conf.json"
    b_path = Path.home() / ".config" / "vscodium-dockerfied" / "conf.json"
    _, a = load_json_if_exists(a_path)
    _, b = load_json_if_exists(b_path)
    return deep_merge(a, b)


def require_capital_keys(section: dict[str, Any], section_name: str) -> None:
    for k in section.keys():
        if not str(k).isupper():
            raise ValueError(f"All keys in {section_name} must be CAPITALIZED. Bad key: {k}")


def require_run_env_vars_present() -> dict[str, str]:
    missing = [k for k in REQUIRED_RUN_ENV_VARS if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables for run: "
            + ", ".join(missing)
            + ".\n"
            + "These must be present in your shell environment before running containers."
        )
    return {k: os.environ[k] for k in REQUIRED_RUN_ENV_VARS}


@dataclass
class Config:
    repo_root: Path

    skip_build: bool

    standalone_args: dict[str, Any]
    remoss_args: dict[str, Any]

    docker_build_args: dict[str, str]  # must include VSCODIUM_VER, CLIENT_USERNAME (CAPS keys)
    docker_run_args: dict[str, str]  # must include HOST_* (CAPS keys)

    @staticmethod
    def load(repo_root: Path, args: argparse.Namespace) -> "Config":
        cfg = load_config()

        skip_build = bool(cfg.get("skip_build", False))

        standalone_args = cfg.get("standalone_args", {}) or {}
        remoss_args = cfg.get("remoss_args", {}) or {}
        docker_build_args = cfg.get("docker_build_args", {}) or {}
        docker_run_args = cfg.get("docker_run_args", {}) or {}

        if not isinstance(standalone_args, dict):
            raise ValueError("standalone_args must be an object")
        if not isinstance(remoss_args, dict):
            raise ValueError("remoss_args must be an object")
        if not isinstance(docker_build_args, dict):
            raise ValueError("docker_build_args must be an object")
        if not isinstance(docker_run_args, dict):
            raise ValueError("docker_run_args must be an object")

        docker_build_args = {str(k): str(v) for k, v in docker_build_args.items()}
        docker_run_args = {str(k): str(v) for k, v in docker_run_args.items()}

        require_capital_keys(docker_build_args, "docker_build_args")
        require_capital_keys(docker_run_args, "docker_run_args")

        # CLI overrides (override JSON)
        if args.skip_build is not None:
            skip_build = args.skip_build

        if args.vscodium_ver is not None:
            docker_build_args["VSCODIUM_VER"] = args.vscodium_ver
        if args.client_username is not None:
            docker_build_args["CLIENT_USERNAME"] = args.client_username

        if args.host_workspace is not None:
            docker_run_args["HOST_WORKSPACE"] = args.host_workspace
        if args.host_vscodium_config_dir is not None:
            docker_run_args["HOST_VSCODIUM_CONFIG_DIR"] = args.host_vscodium_config_dir
        if args.host_vscodium_vscode_oss_dir is not None:
            docker_run_args["HOST_VSCODIUM_VSCODE_OSS_DIR"] = args.host_vscodium_vscode_oss_dir

        # Optional CLI override for network per-mode
        if args.standalone_network is not None:
            standalone_args["network"] = args.standalone_network
        if args.remoss_network is not None:
            remoss_args["network"] = args.remoss_network

        # Validate required keys
        for k in ["VSCODIUM_VER", "CLIENT_USERNAME"]:
            if k not in docker_build_args or not docker_build_args[k]:
                raise KeyError(f"Missing required docker_build_args.{k}")

        for k in ["HOST_WORKSPACE", "HOST_VSCODIUM_CONFIG_DIR", "HOST_VSCODIUM_VSCODE_OSS_DIR"]:
            if k not in docker_run_args or not docker_run_args[k]:
                raise KeyError(f"Missing required docker_run_args.{k}")

        # Validate supported mode args
        for section_name, section in [("standalone_args", standalone_args), ("remoss_args", remoss_args)]:
            if "network" in section and section["network"] is not None and not isinstance(section["network"], str):
                raise ValueError(f"{section_name}.network must be a string when set")

        return Config(
            repo_root=repo_root,
            skip_build=skip_build,
            standalone_args=standalone_args,
            remoss_args=remoss_args,
            docker_build_args=docker_build_args,
            docker_run_args=docker_run_args,
        )


def image_name(target: str, vscodium_ver: str) -> str:
    return f"vscodium-dockerfied-{target}-{vscodium_ver}.img:latest"


def docker_build_arg_flags(build_args: dict[str, str], extra: None | dict[str, str] = None) -> list[str]:
    merged = dict(build_args)
    if extra:
        merged.update(extra)
    flags: list[str] = []
    for k, v in merged.items():
        flags += ["--build-arg", f"{k}={v}"]
    return flags


def mode_network_args(_mode: str, mode_args: dict[str, Any], default_network: None | str) -> list[str]:
    """
    Translate mode_args.network into `docker run --network <value>`.
    If not set, uses default_network (if provided), otherwise empty.
    """
    network = mode_args.get("network", None)
    if network is None or network == "":
        network = default_network
    if network is None or network == "":
        return []
    return ["--network", str(network)]


def build_base(cfg: Config) -> None:
    workdir = cfg.repo_root / "vscodium-dockerfied-base"
    dockerfile = "Dockerfile.vscodium-dockerfied-base"
    v = cfg.docker_build_args["VSCODIUM_VER"]
    tag = image_name("base", v)

    cmd = [
        "docker", "build",
        "-f", dockerfile,
        "-t", tag,
        *docker_build_arg_flags(cfg.docker_build_args, extra={"VSCODIUM_VERSION": v}),
        ".",
    ]
    run_cmd(["ls", "-alt"], cwd=workdir)
    run_cmd(cmd, cwd=workdir, extra_env={"DOCKER_BUILDKIT": "1"})


def build_standalone(cfg: Config) -> None:
    workdir = cfg.repo_root / "vscodium-dockerfied-standalone"
    dockerfile = "Dockerfile.vscodium-dockerfied-standalone"
    v = cfg.docker_build_args["VSCODIUM_VER"]
    tag = image_name("standalone", v)

    cmd = [
        "docker", "build",
        "-f", dockerfile,
        "-t", tag,
        *docker_build_arg_flags(cfg.docker_build_args),
        ".",
    ]
    run_cmd(["ls", "-alt"], cwd=workdir)
    run_cmd(cmd, cwd=workdir, extra_env={"DOCKER_BUILDKIT": "1"})


def build_remoss_client(cfg: Config) -> None:
    workdir = cfg.repo_root / "vscodium-dockerfied-remoss-client"
    dockerfile = "Dockerfile.vscodium-dockerfied-remoss-client"
    v = cfg.docker_build_args["VSCODIUM_VER"]
    tag = image_name("remoss-client", v)

    cmd = [
        "docker", "build",
        "-f", dockerfile,
        "-t", tag,
        *docker_build_arg_flags(cfg.docker_build_args),
        ".",
    ]
    run_cmd(["ls", "-alt"], cwd=workdir)
    run_cmd(cmd, cwd=workdir, extra_env={"DOCKER_BUILDKIT": "1"})


def show_images() -> None:
    run_cmd(["docker", "image", "ls", "--format", "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}"])


def run_standalone(cfg: Config) -> None:
    env = require_run_env_vars_present()

    workdir = cfg.repo_root / "vscodium-dockerfied-standalone"
    v = cfg.docker_build_args["VSCODIUM_VER"]
    user = cfg.docker_build_args["CLIENT_USERNAME"]
    img = image_name("standalone", v)

    run_args = cfg.docker_run_args
    network_args = mode_network_args("standalone", cfg.standalone_args, default_network=None)

    cmd = [
        "docker", "run", "--rm",
        "--name", "vscodium-dockerfied-base",
        *network_args,
        "--shm-size=2gb",
        "-e", "DISPLAY=:0",
        "-e", f"WAYLAND_DISPLAY={env['WAYLAND_DISPLAY']}",
        "-e", "XDG_RUNTIME_DIR=/tmp/runtime-docker",
        "-e", f"PULSE_SERVER=unix:{env['XDG_RUNTIME_DIR']}/pulse/native",
        "-e", "XAUTHORITY=/tmp/.Xauthority",
        "-e", "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus",
        "-e", "DOCKER_BUILDKIT=1",
        "-v", f"{run_args['HOST_VSCODIUM_CONFIG_DIR']}:/home/{user}/.config/VSCodium",
        "-v", f"{run_args['HOST_VSCODIUM_VSCODE_OSS_DIR']}:/home/{user}/.vscode-oss",
        "-v", "/tmp/.X11-unix:/tmp/.X11-unix",
        "-v", f"{env['XAUTHORITY']}:/tmp/.Xauthority:ro",
        "-v", f"{env['XDG_RUNTIME_DIR']}/{env['WAYLAND_DISPLAY']}:/tmp/runtime-docker/{env['WAYLAND_DISPLAY']}",
        "-v", f"{run_args['HOST_WORKSPACE']}:/workspace",
        "-v", "/run/user/1000/bus:/run/user/1000/bus",
        "-v", f"{env['XDG_RUNTIME_DIR']}/pulse:/tmp/runtime-docker/pulse",
        img,
    ]
    run_cmd(["ls", "-alt"], cwd=workdir)
    run_cmd(cmd, cwd=workdir)


def run_remoss_client(cfg: Config) -> None:
    env = require_run_env_vars_present()

    workdir = cfg.repo_root / "vscodium-dockerfied-remoss-client"
    v = cfg.docker_build_args["VSCODIUM_VER"]
    user = cfg.docker_build_args["CLIENT_USERNAME"]
    img = image_name("remoss-client", v)

    run_args = cfg.docker_run_args
    # original script defaulted to host; preserve that unless overridden
    network_args = mode_network_args("remoss", cfg.remoss_args, default_network="host")

    cmd = [
        "docker", "run", "--rm",
        "--name", "vscodium-dockerfied-remoss-client",
        *network_args,
        "--shm-size=2gb",
        "-e", "DISPLAY=:0",
        "-e", f"WAYLAND_DISPLAY={env['WAYLAND_DISPLAY']}",
        "-e", "XDG_RUNTIME_DIR=/tmp/runtime-docker",
        "-e", f"PULSE_SERVER=unix:{env['XDG_RUNTIME_DIR']}/pulse/native",
        "-e", "XAUTHORITY=/tmp/.Xauthority",
        "-e", "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus",
        "-e", "DOCKER_BUILDKIT=1",
        "-v", f"{run_args['HOST_VSCODIUM_CONFIG_DIR']}:/home/{user}/.config/VSCodium",
        "-v", f"{run_args['HOST_VSCODIUM_VSCODE_OSS_DIR']}:/home/{user}/.vscode-oss",
        "-v", "/tmp/.X11-unix:/tmp/.X11-unix",
        "-v", f"{env['XAUTHORITY']}:/tmp/.Xauthority:ro",
        "-v", f"{env['XDG_RUNTIME_DIR']}/{env['WAYLAND_DISPLAY']}:/tmp/runtime-docker/{env['WAYLAND_DISPLAY']}",
        "-v", f"{run_args['HOST_WORKSPACE']}:/workspace",
        "-v", "/run/user/1000/bus:/run/user/1000/bus",
        "-v", f"{env['XDG_RUNTIME_DIR']}/pulse:/tmp/runtime-docker/pulse",
        img,
    ]
    run_cmd(["ls", "-alt"], cwd=workdir)
    run_cmd(cmd, cwd=workdir)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vscodium-dockerfied.py")
    sub = p.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build docker images")
    p_build.add_argument("target", choices=["standalone", "remoss", "base"], help="What to build")
    p_build.add_argument("--skip-build", dest="skip_build", action=argparse.BooleanOptionalAction, default=None)

    p_run = sub.add_parser("run", help="Run docker images (builds first by default unless skip_build=true)")
    p_run.add_argument("mode", choices=["standalone", "remoss"], help="Which runtime to use")
    p_run.add_argument("--skip-build", dest="skip_build", action=argparse.BooleanOptionalAction, default=None)

    for sp in (p_build, p_run):
        sp.add_argument("--vscodium-ver", dest="vscodium_ver", default=None)
        sp.add_argument("--client-username", dest="client_username", default=None)
        sp.add_argument("--host-workspace", dest="host_workspace", default=None)
        sp.add_argument("--host-vscodium-config-dir", dest="host_vscodium_config_dir", default=None)
        sp.add_argument("--host-vscodium-vscode-oss-dir", dest="host_vscodium_vscode_oss_dir", default=None)

        sp.add_argument("--standalone-network", dest="standalone_network", default=None, help="Overrides standalone_args.network")
        sp.add_argument("--remoss-network", dest="remoss_network", default=None, help="Overrides remoss_args.network")

    return p


def main(argv: Sequence[str]) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parent
    cfg = Config.load(repo_root, args)

    if args.command == "build":
        if cfg.skip_build:
            eprint("skip_build=true; build command will not build anything.")
            return 0

        if args.target == "base":
            build_base(cfg)
        elif args.target == "standalone":
            build_base(cfg)
            build_standalone(cfg)
        elif args.target == "remoss":
            build_base(cfg)
            build_remoss_client(cfg)
        else:
            raise ValueError(args.target)

        show_images()
        return 0

    if args.command == "run":
        if not cfg.skip_build:
            build_base(cfg)
            if args.mode == "standalone":
                build_standalone(cfg)
            else:
                build_remoss_client(cfg)
            show_images()

        if args.mode == "standalone":
            run_standalone(cfg)
        else:
            run_remoss_client(cfg)

        return 0

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))