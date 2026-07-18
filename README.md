```markdown
# vscodium-dockerfied

Build and run VSCodium in Docker (either **standalone** or a **remoss client**) from a single Python entrypoint.

This project is intended to make it easy to:
- Build the required Docker images with consistent build args.
- Run VSCodium containers with the needed Wayland/X11 plumbing.
- Launch **multiple containers** without name collisions (container names include a timestamp + PID suffix).
- Keep startup output clean by default, with an optional **verbose** mode.
- Switch between different sets of configuration using a simple **Configuration ID** (`--conf-id`).

## Requirements

- Python 3.10+ (script uses modern type hints)
- Docker (BuildKit recommended)
- Linux desktop environment supporting Wayland/X11 (your setup may vary)

### Environment variables required for `run`

Before running containers, these must be set in your shell environment:

- `XDG_RUNTIME_DIR`
- `WAYLAND_DISPLAY`
- `XAUTHORITY`

If any are missing, `run` will fail with a clear error.

## Configuration

Config is loaded/merged in this order:

1. `./vscodium-dockerfied.conf.json`   ← current directory
2. `~/.config/vscodium-dockerfied/vscodium-dockerfied.conf.json`   ← overrides #1 if both exist
3. CLI flags override everything

### Configuration IDs

If you pass `--conf-id <id>` on the command line, the config file names change to:

- `./vscodium-dockerfied.conf.<id>.json`
- `~/.config/vscodium-dockerfied/vscodium-dockerfied.conf.<id>.json`

This allows you to maintain multiple independent configurations (e.g., `home`, `work`, `testing`) without juggling separate files manually. When no `--conf-id` is provided, the default filenames above are used (same as before).

The `--conf-id` flag is **global** – you can add it to any command, for example:

```bash
./vscodium-dockerfied.py --conf-id work run standalone
./vscodium-dockerfied.py --conf-id testing build base
```

### Example config

```json
{
  "skip_build": false,
  "verbose": false,
  "standalone_args": { "network": "none" },
  "remoss_args": {},
  "docker_build_args": {
    "VSCODIUM_VER": "1.109.41146",
    "CLIENT_USERNAME": "codium"
  },
  "docker_run_args": {
    "HOST_WORKSPACE": "~/github",
    "HOST_VSCODIUM_CONFIG_DIR": "~/.config/VSCodium2",
    "HOST_VSCODIUM_VSCODE_OSS_DIR": "~/.vscode-oss.VSCodium2"
  }
}
```

**Note:** The version string (`VSCODIUM_VER`) must match a VSCodium release you intend to build. Change it if you want a different version.

### Important: new host directories for VSCodium config

When you point `HOST_VSCODIUM_CONFIG_DIR` or `HOST_VSCODIUM_VSCODE_OSS_DIR` to a path that **does not yet exist on the host**, Docker will automatically create that directory as `root` when it mounts it (this is standard Docker behaviour). VSCodium inside the container runs as the non‑root user (e.g. `codium`) and may then be unable to write to the directory, causing the application to fail to start or lose configuration.

To avoid this, **manually create the target directory before the first run** with your own user ownership. For example:

```bash
mkdir -p ~/.config/VSCodium2
```

or

```bash
mkdir -p ~/.vscode-oss.VSCodium2
```

Then run the container as usual. The directory will already exist and be owned by your host user, allowing the container user to write to it via the user namespace mapping.

> This step is only required on the **first launch** with a new directory, or when switching to a configuration ID that references new paths.

### Path expansion (`~` and `$VARS`)

Values under `docker_run_args` (and corresponding CLI overrides) support:
- `~` expansion (interpreted as `$HOME`)
- `$VARS` expansion (via standard shell-style env var substitution)

Example:

```json
"HOST_WORKSPACE": "~/github"
```

becomes:

```text
/home/you/github
```

## Usage

### Build images

Build base only:

```bash
./vscodium-dockerfied.py build base
```

Build standalone (base + standalone):

```bash
./vscodium-dockerfied.py build standalone
```

Build remoss client (base + remoss-client):

```bash
./vscodium-dockerfied.py build remoss
```

Add `--conf-id` to use an alternate configuration:

```bash
./vscodium-dockerfied.py --conf-id myother build standalone
```

### Run (detached)

Run standalone:

```bash
./vscodium-dockerfied.py run standalone
```

Run remoss client:

```bash
./vscodium-dockerfied.py run remoss
```

#### Multiple containers

Containers are started with a unique name suffix:

```text
vscodium-dockerfied-standalone-YYYYMMDD-HHMMSS-PID
vscodium-dockerfied-remoss-client-YYYYMMDD-HHMMSS-PID
```

This allows launching multiple instances without Docker name collisions.

## Output / verbosity

- **Default (quiet):** prints only the created container name (suitable for scripting)
- **Verbose:** shows docker build/run output (and hides extra noise like `ls ...`)

Enable verbose:

```bash
./vscodium-dockerfied.py --verbose run standalone
```

You can also set `"verbose": true` in the config file.

## Networking options (per mode)

Supported config keys:

- `standalone_args.network`: passed as `docker run --network <value>` (no default)
- `remoss_args.network`: passed as `docker run --network <value>` (defaults to `"host"` if not provided)

You can override via CLI:

```bash
./vscodium-dockerfied.py run standalone --standalone-network none
./vscodium-dockerfied.py run remoss --remoss-network host
```

## Stopping containers

Since containers run detached (`-d`), stop them with:

```bash
docker stop <container_name>
```

They are started with `--rm`, so they will be removed automatically after stopping.

## Notes / troubleshooting

- If you see GUI or audio issues, verify that your `XDG_RUNTIME_DIR`, `WAYLAND_DISPLAY`, and `XAUTHORITY` are correct for your session.
- If you change `VSCODIUM_VER`, you’ll likely need to rebuild images (unless you set `skip_build=true` intentionally).
- Use the `--conf-id` flag to experiment with different setups without editing the default config file.
- If a container starts but immediately disappears (and you used `--rm`), the application may be crashing silently. Temporarily remove `--rm` or run interactively with a shell to debug (see script’s help).
- **Directory permissions:** See the [Important](#important-new-host-directories-for-vscodium-config) note above about creating new host config directories with correct ownership before the first run.

## License

See the LICENSE file
```