#!/bin/bash
set -e

# was installed by vscodium-dockerfied-base, initializes codium configuration in case there isn't one
/usr/local/bin/vscodium-init-config.sh
# was installed by vscodium-dockerfied-base, waits for codium to quit
/usr/local/bin/start-vscodium-base.sh
