
#!/bin/bash
set -euo pipefail
set -x

# cd to the directory where this script lives
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
source env.sh

cd vscodium-dockerfied-standalone
ls -alt

#HOST_WORKSPACE="/home/craig/github"

docker run --rm \
  --name vscodium-dockerfied-base \
  --shm-size=2gb \
  -e DISPLAY=:0 \
  -e WAYLAND_DISPLAY="${WAYLAND_DISPLAY}" \
  -e XDG_RUNTIME_DIR=/tmp/runtime-docker \
  -e PULSE_SERVER="unix:${XDG_RUNTIME_DIR}/pulse/native" \
  -e XAUTHORITY=/tmp/.Xauthority \
  -e DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus" \
  -e DOCKER_BUILDKIT=1 \
  -v "${HOST_VSCODIUM_CONFIG_DIR}":"/home/${CLIENT_USERNAME}/.config/VSCodium" \
  -v "${HOST_VSCODIUM_VSCODE_OSS_DIR}":"/home/${CLIENT_USERNAME}/.vscode-oss" \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "${XAUTHORITY}":/tmp/.Xauthority:ro \
  -v "${XDG_RUNTIME_DIR}/${WAYLAND_DISPLAY}":"/tmp/runtime-docker/${WAYLAND_DISPLAY}" \
  -v "${HOST_WORKSPACE}":/workspace \
  -v /run/user/1000/bus:/run/user/1000/bus \
  -v "${XDG_RUNTIME_DIR}/pulse":/tmp/runtime-docker/pulse \
  vscodium-dockerfied-standalone-${VSCODIUM_VER}.img:latest
