#!/bin/bash
set -xe

# was installed by vscodium-dockerfied-base, initializes codium configuration in case there isn't one
/usr/local/bin/vscodium-init-config.sh

# modify the setting etc. for the remote oss (by xaberus) extension
/usr/local/bin/config-vscode-oss-argv-json.sh

# was installed by vscodium-dockerfied-base, waits for codium to quit
/usr/local/bin/start-vscodium-base.sh
