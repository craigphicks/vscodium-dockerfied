#!/bin/bash
set -x
set -euo pipefail

# cd to the directory where this script lives
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
source env.sh

cd vscodium-dockerfied-base
ls -alt

#VSCODIUM_VER="1.109.41146"

DOCKER_BUILDKIT=1 docker build \
  -f Dockerfile.vscodium-dockerfied-base \
  -t "vscodium-dockerfied-base-${VSCODIUM_VER}.img:latest" \
  --build-arg "VSCODIUM_VERSION=${VSCODIUM_VER}" \
  .

# Show the resulting image
docker image ls --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}" \
  | grep -F "vscodium-dockerfied-base-${VSCODIUM_VER}.img"

