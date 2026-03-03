#!/bin/bash
set -euo pipefail
set -x

# cd to the directory where this script lives
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
source env.sh

cd vscodium-dockerfied-standalone
ls -alt

#VSCODIUM_VER="1.109.41146"

DOCKER_BUILDKIT=1 docker build \
  -f Dockerfile.vscodium-dockerfied-standalone \
  -t "vscodium-dockerfied-standalone-${VSCODIUM_VER}.img:latest" \
  --build-arg "CLIENT_USERNAME=codium" \
  --build-arg "VSCODIUM_VER=${VSCODIUM_VER}" \
  .

# Show the resulting image
docker image ls --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}" \
| grep vscodium-dockerfied-standalone-${VSCODIUM_VER}

