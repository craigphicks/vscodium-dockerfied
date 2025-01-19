#!/bin/bash
set -e  # Exit on error

DOCKER_IMAGE_NAME=vscodium-dockerfied.img
DOCKER_CONTAINER_NAME=vscodium-dockerfied
VSCODIUM_CONFIG_DIR=${HOME}/.config/${DOCKER_CONTAINER_NAME}

# Parse arguments
BUILD_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--build)
            if [ -z "$2" ]; then
                echo "Error: Build directory not specified after $1"
                exit 1
            fi
            BUILD_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [-b|--build <dockerfile-directory>]"
            exit 1
            ;;
    esac
done

# Build image if requested
if [ -n "$BUILD_DIR" ]; then
    if [ ! -d "$BUILD_DIR" ]; then
        echo "Error: Build directory '$BUILD_DIR' does not exist"
        exit 1
    fi
    echo "Building Docker image from $BUILD_DIR..."
    docker build -t ${DOCKER_IMAGE_NAME} "$BUILD_DIR"
fi

# Enable X access control
xhost +local:root >/dev/null 2>&1

mkdir -p ${VSCODIUM_CONFIG_DIR}


# if container of same name exists (running or stopped), remove it
if [ "$(docker ps -aq -f name=vscodium-dockered)" ]; then
    docker rm -f vscodium-dockered
fi

# Many of the arguments to 'docker run' below are necessary to enable VSCodium 
# to run in the container with access to the host display.
# This was only tested with host being Debian 12 running Wayland with an X shim 
# (which is the default for Debian12).
# Other settups may require different arguments.
docker run \
    -d \
    --rm \
    --name vscodium-dockered \
    --user 1000:1000 \
    --security-opt seccomp=unconfined \
    --network host \
    -e DISPLAY=:0 \
    -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
    -e XDG_RUNTIME_DIR=/tmp/runtime-docker \
    -e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \
    -e XAUTHORITY=/tmp/.Xauthority \
    -e DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $XAUTHORITY:/tmp/.Xauthority:ro \
    -v $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY:/tmp/runtime-docker/$WAYLAND_DISPLAY \
    -v ${VSCODIUM_CONFIG_DIR}:/home/ubuntu/.config/VSCodium \
    -v $(pwd):/workspace \
    -v /run/user/1000/bus:/run/user/1000/bus \
    ${DOCKER_IMAGE_NAME} /workspace